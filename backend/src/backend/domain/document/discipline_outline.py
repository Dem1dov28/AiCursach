"""Discipline-specific coursework outlines and methods-chapter helpers."""

from __future__ import annotations

import re
from typing import Any

_METHODS_RE = re.compile(
    r"(метод|methodology|методик|исследован|расч[её]т|аналитическ)",
    re.I,
)

# Numbered chapter lines suitable for Writer multipass.
DISCIPLINE_CHAPTERS: dict[str, list[str]] = {
    "programming": [
        "1 АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ",
        "2 МЕТОДЫ И СРЕДСТВА РАЗРАБОТКИ",
        "3 ПРОЕКТИРОВАНИЕ РЕШЕНИЯ",
        "4 РЕАЛИЗАЦИЯ И ТЕСТИРОВАНИЕ",
    ],
    "economics": [
        "1 ТЕОРЕТИЧЕСКИЕ ОСНОВЫ ИССЛЕДОВАНИЯ",
        "2 МЕТОДЫ И МЕТОДИКА АНАЛИЗА",
        "3 АНАЛИЗ И РАСЧЁТЫ ПО ТЕМЕ",
        "4 РЕКОМЕНДАЦИИ И ЭКОНОМИЧЕСКАЯ ОЦЕНКА",
    ],
    "management": [
        "1 ТЕОРЕТИЧЕСКИЕ ОСНОВЫ УПРАВЛЕНИЯ",
        "2 МЕТОДЫ ИССЛЕДОВАНИЯ И АНАЛИЗА",
        "3 АНАЛИЗ ОБЪЕКТА УПРАВЛЕНИЯ",
        "4 ПРЕДЛОЖЕНИЯ ПО СОВЕРШЕНСТВОВАНИЮ",
    ],
    "humanities": [
        "1 ТЕОРЕТИЧЕСКИЕ ОСНОВЫ ТЕМЫ",
        "2 МЕТОДЫ ИССЛЕДОВАНИЯ",
        "3 АНАЛИЗ МАТЕРИАЛА",
        "4 ВЫВОДЫ И ОБОБЩЕНИЯ",
    ],
    "engineering": [
        "1 АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ",
        "2 МЕТОДЫ И СРЕДСТВА РЕШЕНИЯ",
        "3 ПРОЕКТИРОВАНИЕ И РАСЧЁТЫ",
        "4 РЕАЛИЗАЦИЯ И ПРОВЕРКА",
    ],
    "general": [
        "1 ТЕОРЕТИЧЕСКИЕ ОСНОВЫ",
        "2 МЕТОДЫ ИССЛЕДОВАНИЯ",
        "3 ОСНОВНАЯ ЧАСТЬ И РЕЗУЛЬТАТЫ",
    ],
}

OUTLINE_TEMPLATES: dict[str, str] = {
    "programming": (
        "Введение\n"
        "1 Анализ предметной области\n"
        "2 Методы и средства разработки\n"
        "3 Проектирование решения\n"
        "4 Реализация и тестирование\n"
        "Заключение\n"
        "Список использованных источников\n"
        "Приложения"
    ),
    "economics": (
        "Введение\n"
        "1 Теоретические основы исследования\n"
        "2 Методы и методика анализа\n"
        "3 Анализ и расчёты по теме\n"
        "4 Рекомендации и экономическая оценка\n"
        "Заключение\n"
        "Список использованных источников\n"
        "Приложения"
    ),
    "management": (
        "Введение\n"
        "1 Теоретические основы управления\n"
        "2 Методы исследования и анализа\n"
        "3 Анализ объекта управления\n"
        "4 Предложения по совершенствованию\n"
        "Заключение\n"
        "Список использованных источников\n"
        "Приложения"
    ),
    "humanities": (
        "Введение\n"
        "1 Теоретические основы темы\n"
        "2 Методы исследования\n"
        "3 Анализ материала\n"
        "4 Выводы и обобщения\n"
        "Заключение\n"
        "Список использованных источников"
    ),
    "engineering": (
        "Введение\n"
        "1 Анализ предметной области\n"
        "2 Методы и средства решения\n"
        "3 Проектирование и расчёты\n"
        "4 Реализация и проверка\n"
        "Заключение\n"
        "Список использованных источников\n"
        "Приложения"
    ),
    "general": (
        "Введение\n"
        "1 Теоретические основы\n"
        "2 Методы исследования\n"
        "3 Основная часть и результаты\n"
        "Заключение\n"
        "Список использованных источников"
    ),
}


def default_chapter_titles(discipline: str | None, *, max_chapters: int = 5) -> list[str]:
    key = (discipline or "general").strip().lower()
    titles = DISCIPLINE_CHAPTERS.get(key) or DISCIPLINE_CHAPTERS["general"]
    return titles[:max_chapters]


def outline_template_for_discipline(discipline: str | None) -> str:
    key = (discipline or "general").strip().lower()
    return OUTLINE_TEMPLATES.get(key) or OUTLINE_TEMPLATES["general"]


def text_has_methods_chapter(text: str) -> bool:
    for line in (text or "").splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if _METHODS_RE.search(cleaned) and (
            re.match(r"^\d+", cleaned)
            or cleaned.isupper()
            or re.match(r"^(глава|раздел)\b", cleaned, re.I)
        ):
            return True
        if _METHODS_RE.search(cleaned) and len(cleaned) < 80:
            return True
    return False


def draft_has_methods_chapter(draft: dict[str, Any] | None) -> bool:
    if not isinstance(draft, dict):
        return False
    sections = draft.get("sections") or []
    if not isinstance(sections, list):
        return False
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title") or "")
        if _METHODS_RE.search(title):
            return True
    return False


def ensure_methods_in_outline(structure_outline: str, discipline: str | None) -> str:
    """If outline lacks a methods chapter, inject a discipline-appropriate one."""
    text = (structure_outline or "").strip()
    if text_has_methods_chapter(text):
        return text
    if not text:
        return outline_template_for_discipline(discipline)

    methods_line = {
        "programming": "2 Методы и средства разработки",
        "economics": "2 Методы и методика анализа",
        "management": "2 Методы исследования и анализа",
        "humanities": "2 Методы исследования",
        "engineering": "2 Методы и средства решения",
    }.get((discipline or "general").strip().lower(), "2 Методы исследования")

    lines = text.splitlines()
    insert_at = 1
    for i, line in enumerate(lines):
        if re.match(r"^1[\.\):\s]", line.strip()) or re.match(
            r"^1\s+[А-ЯA-Z]", line.strip()
        ):
            insert_at = i + 1
            break
        if "введен" in line.lower():
            insert_at = i + 1
    lines.insert(insert_at, methods_line)
    return "\n".join(lines)
