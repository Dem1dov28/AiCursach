"""AnnexBuilder — план приложений (буквы, заголовки, подписи) для курсовой."""

from __future__ import annotations

import json

from backend.core.paths import REPO_ROOT
from backend.domain.document.annex_plan import (
    annex_plan_issues,
    inventory_png_entries,
    normalize_annex_plan,
    reassign_letters_avoiding,
)
from backend.domain.workflow.work_profile import uses_coursework_docx
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.docx_images import (
    build_heuristic_annex_plan,
    collect_project_pngs,
)
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import ANNEX_PLAN_PROMPT


def annex_builder_node(state: WorkState) -> dict:
    coursework = uses_coursework_docx(dict(state))
    needs = bool(state.get("needs_annexes", coursework))
    project_name = state.get("project_name", "WorkProject")
    logs: list[str] = []

    if not (coursework and needs):
        logs.append("AnnexBuilder: skipped (не требуется)")
        result = {
            "tool_log": logs,
            "annex_plan_done": True,
            "annex_builder_attempts": 0,
            "annex_plan": "",
        }
        result.update(gate_after_llm(state, "annex_builder", {}))
        return result

    pngs = collect_project_pngs(project_name)
    if not pngs:
        logs.append("AnnexBuilder: нет PNG — пустой план, done")
        result = {
            "tool_log": logs,
            "annex_plan_done": True,
            "annex_builder_attempts": 0,
            "annex_plan": json.dumps({"appendices": []}, ensure_ascii=False),
        }
        result.update(gate_after_llm(state, "annex_builder", {}))
        return result

    inventory = inventory_png_entries(pngs, project_root=REPO_ROOT)
    plan, llm_payload, llm_logs = _llm_annex_plan(state, inventory)
    logs.extend(llm_logs)
    reserved = {
        str(x).strip().upper().replace("Ё", "Е")
        for x in (state.get("annex_reserved_letters") or [])
        if str(x).strip()
    }

    if annex_plan_issues(plan):
        logs.append("AnnexBuilder: LLM-план невалиден — heuristic fallback")
        plan = build_heuristic_annex_plan(
            pngs,
            project_root=REPO_ROOT,
            reserved_letters=reserved,
        )
        plan = normalize_annex_plan(plan)
    elif reserved:
        plan = reassign_letters_avoiding(plan, reserved)
        logs.append(f"AnnexBuilder: буквы сдвинуты (занято: {', '.join(sorted(reserved))})")

    issues = annex_plan_issues(plan)
    attempts = int(state.get("annex_builder_attempts") or 0)
    if issues:
        attempts += 1
        logs.append("AnnexBuilder: " + "; ".join(issues))
        result = {
            "tool_log": logs,
            "annex_plan_done": False,
            "annex_builder_attempts": attempts,
            "annex_plan": json.dumps(plan, ensure_ascii=False),
        }
    else:
        n_figs = sum(len(a.get("figures") or []) for a in plan.get("appendices") or [])
        logs.append(
            f"AnnexBuilder: приложений={len(plan.get('appendices') or [])}, рисунков={n_figs}"
        )
        result = {
            "tool_log": logs,
            "annex_plan_done": True,
            "annex_builder_attempts": 0,
            "annex_plan": json.dumps(plan, ensure_ascii=False),
        }

    result.update(gate_after_llm(state, "annex_builder", llm_payload))
    return result


def _llm_annex_plan(
    state: WorkState,
    inventory: list[dict[str, str]],
) -> tuple[dict, dict, list[str]]:
    logs: list[str] = []
    inv_text = json.dumps(inventory, ensure_ascii=False, indent=2)[:6000]
    llm = get_llm(temperature=0.2)
    prompt = ANNEX_PLAN_PROMPT.format(
        topic=state.get("topic", "") or "",
        requirements=(state.get("requirements") or "")[:3000],
        structure_outline=(state.get("structure_outline") or "")[:2000],
        png_inventory=inv_text or "[]",
    )
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {}
    plan = normalize_annex_plan(data)
    if annex_plan_issues(plan):
        logs.append("AnnexBuilder LLM: план с проблемами")
    else:
        logs.append(f"AnnexBuilder LLM: appendices={len(plan.get('appendices') or [])}")
    return plan, data if isinstance(data, dict) else {}, logs
