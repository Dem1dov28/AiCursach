"""Diagrammer — автогенерация PlantUML и IDEF0 с валидацией рендера."""

from __future__ import annotations

import json

from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import DIAGRAMMER_FIX_PROMPT, DIAGRAMMER_PROMPT
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.text_utils import as_text
from backend.infrastructure.adapters.diagram_gen import (
    apply_diagram_package,
    diagrams_render_success,
    png_paths,
)
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm

_MAX_RENDER_ATTEMPTS = 3


def _build_prompt(state: WorkState, types_str: str) -> str:
    return DIAGRAMMER_PROMPT.format(
        topic=state.get("topic", ""),
        requirements=state.get("requirements", ""),
        diagram_types=types_str,
        structure_outline=state.get("structure_outline", ""),
        content_draft=(state.get("content_draft") or "")[:6000],
    )


def diagrammer_node(state: WorkState) -> dict:
    project_name = state.get("project_name", "WorkProject")

    types = state.get("diagram_types", "usecase, idef0")
    if isinstance(types, list):
        types_str = ", ".join(as_text(item) for item in types)
    else:
        types_str = str(types)

    llm = get_llm()
    prompt = _build_prompt(state, types_str)
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {}

    if not data.get("plantuml") and not data.get("idef0"):
        attempts = int(state.get("diagrammer_attempts") or 0) + 1
        result = {
            "diagrams_generated": False,
            "diagrammer_attempts": attempts,
            "tool_log": ["Diagrammer: LLM не вернул диаграммы"],
        }
        result.update(gate_after_llm(state, "diagrammer", data))
        return result

    logs: list[str] = []
    all_files: list[str] = []
    render_ok = False
    render_error = ""

    for attempt in range(1, _MAX_RENDER_ATTEMPTS + 1):
        files, attempt_logs, render_ok, render_error = apply_diagram_package(project_name, data)
        all_files = files
        logs.extend(f"Попытка {attempt}: {line}" for line in attempt_logs)
        if render_ok or not data.get("plantuml"):
            break

        fix_prompt = DIAGRAMMER_FIX_PROMPT.format(
            render_error=render_error[:2000],
            diagram_json=json.dumps(data, ensure_ascii=False, indent=2)[:6000],
        )
        fixed_raw = llm_text(llm, fix_prompt)
        fixed = parse_json_from_llm(fixed_raw) or {}
        if fixed.get("plantuml") or fixed.get("idef0"):
            data = fixed
        else:
            logs.append("Diagrammer: LLM не смог исправить PlantUML")
            break

    success = diagrams_render_success(data, all_files=all_files, render_ok=render_ok)
    pngs = png_paths(all_files)
    if not success:
        logs.append(
            f"нет готовых PNG (png={len(pngs)}, render_ok={render_ok}) — не считаем done"
        )
    attempts = int(state.get("diagrammer_attempts") or 0)
    if not success:
        attempts += 1
    result = {
        "diagrams_generated": success,
        "diagrammer_attempts": attempts if not success else 0,
        # В state кладём PNG (+ исходники); done уже зависит только от PNG.
        "diagram_files": all_files,
        "tool_log": [f"Diagrammer: {line}" for line in logs],
    }
    result.update(gate_after_llm(state, "diagrammer", data))
    return result
