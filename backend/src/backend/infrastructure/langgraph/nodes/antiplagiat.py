"""Antiplagiat — оригинальность + скриншот отчёта для приложений."""

from __future__ import annotations

from backend.domain.workflow.work_profile import uses_coursework_docx
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.antiplagiat import (
    clamp_originality_pct,
    find_antiplagiat_screenshot,
)
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm


def antiplagiat_node(state: WorkState) -> dict:
    coursework = uses_coursework_docx(dict(state))
    needs = bool(state.get("needs_antiplagiat", coursework))
    logs: list[str] = []

    if not (coursework and needs):
        logs.append("Antiplagiat: skipped")
        result = {
            "tool_log": logs,
            "antiplagiat_done": True,
            "antiplagiat_attempts": 0,
            "antiplagiat_screenshot": "",
            "annex_reserved_letters": list(state.get("annex_reserved_letters") or []),
        }
        result.update(gate_after_llm(state, "antiplagiat", {}))
        return result

    originality = clamp_originality_pct(state.get("originality_pct"))
    project_name = state.get("project_name", "WorkProject")
    shot = find_antiplagiat_screenshot(project_name)
    skip = _user_skipped_screenshot(state)
    asked = _already_asked(state)

    if shot:
        logs.append(f"Antiplagiat: найден скриншот {shot.name}")
        result = {
            "tool_log": logs,
            "antiplagiat_done": True,
            "antiplagiat_attempts": 0,
            "antiplagiat_screenshot": str(shot),
            "originality_pct": originality,
            "annex_reserved_letters": ["А"],
        }
        result.update(gate_after_llm(state, "antiplagiat", {}))
        return result

    if skip:
        logs.append("Antiplagiat: пользователь продолжил без скриншота")
        result = {
            "tool_log": logs,
            "antiplagiat_done": True,
            "antiplagiat_attempts": 0,
            "antiplagiat_screenshot": "",
            "originality_pct": originality,
            "annex_reserved_letters": [],
        }
        result.update(gate_after_llm(state, "antiplagiat", {}))
        return result

    if not asked and str(state.get("autonomy_level") or "") != "full_auto":
        logs.append("Antiplagiat: скриншот не найден — запрос HITL")
        clarification = {
            "scenario": "missing_data",
            "question": (
                "Положите PNG отчёта «Антиплагиат» в "
                "Материалы/Скриншоты/antiplagiat.png (или файл с именем antiplag*/антиплаг*). "
                "Либо продолжите без скриншота — в тексте останется только заявление об оригинальности."
            ),
            "options": [
                "Продолжить без скриншота",
                "Я положил файл — проверить снова",
            ],
        }
        result = {
            "tool_log": logs,
            "antiplagiat_done": False,
            "antiplagiat_attempts": int(state.get("antiplagiat_attempts") or 0) + 1,
            "antiplagiat_screenshot": "",
            "originality_pct": originality,
            "annex_reserved_letters": [],
        }
        result.update(
            gate_after_llm(
                state,
                "antiplagiat",
                {
                    "confidence": 0.4,
                    "needs_clarification": True,
                    "clarification": clarification,
                },
            )
        )
        return result

    # Already asked or full_auto — finish without screenshot
    logs.append("Antiplagiat: скриншот отсутствует — только originality_pct в реферате")
    result = {
        "tool_log": logs,
        "antiplagiat_done": True,
        "antiplagiat_attempts": 0,
        "antiplagiat_screenshot": "",
        "originality_pct": originality,
        "annex_reserved_letters": [],
    }
    result.update(gate_after_llm(state, "antiplagiat", {}))
    return result


def _already_asked(state: WorkState) -> bool:
    for entry in state.get("clarification_log") or []:
        if isinstance(entry, dict) and entry.get("agent") == "antiplagiat":
            return True
    return False


def _user_skipped_screenshot(state: WorkState) -> bool:
    for entry in reversed(state.get("clarification_log") or []):
        if not isinstance(entry, dict) or entry.get("agent") != "antiplagiat":
            continue
        answer = str(entry.get("answer") or "").lower()
        return "без" in answer
    return False
