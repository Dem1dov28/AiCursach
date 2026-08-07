"""Style Polisher — убирает AI-клише, сохраняя факты и структуру JSON."""

from __future__ import annotations

import json

from backend.domain.style.cliche_checker import validate_style
from backend.domain.workflow.clarification import detect_style_clarification
from backend.domain.workflow.work_profile import writer_uses_coursework_prompt
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import STYLE_POLISHER_PROMPT


def _work_type_label(state: WorkState) -> str:
    if writer_uses_coursework_prompt(state):
        return "coursework"
    return str(state.get("work_type") or "lab")


def style_polisher_node(state: WorkState) -> dict:
    if not state.get("enable_style_polisher", True):
        result = {
            "style_polished": True,
            "style_issues": state.get("style_issues") or [],
            "tool_log": ["Style: полировка отключена в настройках — пропуск"],
        }
        result.update(gate_after_llm(state, "style_polisher", {}))
        return result

    draft = state.get("content_draft", "") or ""
    work_type = _work_type_label(state)

    if not draft.strip():
        result = {
            "style_polished": True,
            "style_issues": [],
            "tool_log": ["Style: черновик пуст — пропуск"],
        }
        result.update(gate_after_llm(state, "style_polisher", {}))
        return result

    issues = validate_style(draft, work_type=work_type)
    if not issues and state.get("style_polished"):
        result = {
            "style_polished": True,
            "style_issues": [],
            "tool_log": ["Style: уже отполирован"],
        }
        result.update(gate_after_llm(state, "style_polisher", {}))
        return result

    cliche_list = ", ".join(f"{item.phrase} ({item.count})" for item in issues) or "не обнаружены"

    llm = get_llm(temperature=0.3)
    prompt = STYLE_POLISHER_PROMPT.format(
        work_type=work_type,
        cliche_list=cliche_list,
        content_draft=draft[:12000],
    )
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw)

    if isinstance(data, dict):
        polished = json.dumps(data, ensure_ascii=False, indent=2)
        remaining = validate_style(polished, work_type=work_type)
        result = {
            "content_draft": polished,
            "style_polished": True,
            "style_polisher_attempts": 0,
            "style_issues": [item.to_dict() for item in remaining],
            "tool_log": [
                f"Style: полировка выполнена (было клише: {len(issues)}, осталось: {len(remaining)})"
            ],
        }
        cliche_count = len(remaining)
        result.update(
            gate_after_llm(
                state,
                "style_polisher",
                data,
                heuristic=lambda s, d, n=cliche_count: detect_style_clarification(s, n),
            )
        )
        return result

    attempts = int(state.get("style_polisher_attempts") or 0) + 1
    result = {
        "style_polished": False,
        "style_polisher_attempts": attempts,
        "style_issues": [item.to_dict() for item in issues],
        "tool_log": ["Style: LLM не вернул JSON — черновик без изменений"],
    }
    cliche_count = len(issues)
    result.update(
        gate_after_llm(
            state,
            "style_polisher",
            {},
            heuristic=lambda s, d, n=cliche_count: detect_style_clarification(s, n),
        )
    )
    return result
