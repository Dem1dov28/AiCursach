"""Work profile inferred by Planner — drives writer mode and team assembly."""

from __future__ import annotations

from typing import Any

VALID_WORK_KINDS = ("lab", "coursework", "diploma", "essay", "report", "unknown")
VALID_DISCIPLINES = (
    "programming",
    "economics",
    "humanities",
    "engineering",
    "management",
    "general",
)


def normalize_work_kind(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in VALID_WORK_KINDS:
        return value
    aliases = {
        "лабораторная": "lab",
        "lab": "lab",
        "курсовая": "coursework",
        "course": "coursework",
        "диплом": "diploma",
        "реферат": "essay",
        "отчёт": "report",
        "отчет": "report",
    }
    return aliases.get(value, "unknown")


def normalize_discipline(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in VALID_DISCIPLINES:
        return value
    if any(k in value for k in ("эконом", "финанс", "бухгал", "маркет")):
        return "economics"
    if any(k in value for k in ("програм", "java", "python", "информ", "it", "software")):
        return "programming"
    if any(k in value for k in ("истор", "филос", "лингв", "прав")):
        return "humanities"
    return "general"


def writer_uses_coursework_prompt(state: dict[str, Any]) -> bool:
    kind = normalize_work_kind(state.get("detected_work_kind") or state.get("work_type"))
    discipline = normalize_discipline(state.get("discipline"))
    if kind in ("coursework", "diploma", "essay"):
        return True
    if kind == "lab" and discipline in ("economics", "humanities", "management"):
        return True
    if state.get("work_type") == "coursework":
        return True
    return bool(state.get("needs_excel") or state.get("needs_charts")) and not state.get("needs_code")


def uses_coursework_docx(state: dict[str, Any]) -> bool:
    """Whether DocxBuilder should assemble a coursework (ПЗ) report, not a lab docx."""
    if state.get("work_type") == "coursework":
        return True
    kind = normalize_work_kind(state.get("detected_work_kind") or "")
    return kind in ("coursework", "diploma", "essay")


def analysis_flags(data: dict[str, Any]) -> dict[str, bool]:
    """Extract boolean needs_* without work_type defaults."""
    return {
        "needs_code": bool(data.get("needs_code", False)),
        "needs_diagrams": bool(data.get("needs_diagrams", False)),
        "needs_excel": bool(data.get("needs_excel", False)),
        "needs_charts": bool(data.get("needs_charts", False)),
        "needs_research": bool(data.get("needs_research", True)),
        "needs_project_init": bool(
            data.get("needs_project_init", data.get("needs_code", False))
        ),
    }
