"""Очистка сгенерированного кода от данных отчёта (ФИО, группа, преподаватель)."""

from __future__ import annotations

from backend.infrastructure.adapters.code_tools import get_code_toolkit
from backend.infrastructure.adapters.source_sanitize import (
    apply_source_sanitize,
    contains_lab_report_text,
    extract_app_only_html,
    sanitize_plain_source,
)

__all__ = [
    "apply_source_sanitize",
    "contains_lab_report_text",
    "extract_app_only_html",
    "sanitize_code_files",
    "sanitize_plain_source",
]


def sanitize_code_files(files: dict[str, str], *, language: str = "") -> dict[str, str]:
    """Языковая санитизация (Java и т.д.) + общая очистка от текста отчёта."""
    base = dict(files)
    if language:
        toolkit = get_code_toolkit(language)
        if toolkit.language == "java":
            base = toolkit.sanitize_files(base)
    return apply_source_sanitize(base)
