"""Проверка и нормализация веб-проекта (HTML/CSS/JS)."""

from __future__ import annotations

import re

from backend.infrastructure.adapters.code_language import normalize_code_language
from backend.infrastructure.adapters.source_sanitize import contains_lab_report_text
from backend.infrastructure.adapters.lab_code import is_code_listing

_HTML_MARKERS = ("<!doctype", "<html", "<head", "<body", "<form", "<input")
_CSS_MARKERS = ("{", "}", ":", "margin", "padding", "display", "flex", "color", "background")
_JS_MARKERS = ("function", "const ", "let ", "var ", "document.", "addEventListener", "=>")
_PROSE_MARKERS = (
    "структура проекта",
    "проект включает",
    "проект состоит",
    "реализован блочный",
    "валидация реализована",
    "папки:",
    "папка css",
)


def _looks_like_html(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    if contains_lab_report_text(text) and not re.search(r"<form\b", text, re.I):
        return False
    if any(m in value for m in _PROSE_MARKERS) and not any(m in value for m in _HTML_MARKERS):
        return False
    return any(m in value for m in _HTML_MARKERS)


def _looks_like_css(text: str) -> bool:
    value = (text or "").strip()
    if len(value) < 10:
        return False
    lower = value.lower()
    if any(m in lower for m in _PROSE_MARKERS):
        return False
    return sum(1 for m in _CSS_MARKERS if m in lower) >= 2


def _looks_like_js(text: str) -> bool:
    value = (text or "").strip()
    if len(value) < 10:
        return False
    lower = value.lower()
    if any(m in lower for m in _PROSE_MARKERS):
        return False
    return any(m in lower for m in _JS_MARKERS)


def _normalize_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def validate_javascript_files(files: dict[str, str]) -> dict[str, str]:
    """Оставить только реальные исходники, отбросить текстовые описания."""
    valid: dict[str, str] = {}
    for raw_name, content in files.items():
        if not isinstance(content, str):
            continue
        name = _normalize_name(raw_name)
        lower = name.lower()
        if lower.endswith((".html", ".htm")):
            if _looks_like_html(content):
                valid[name] = content
        elif lower.endswith(".css"):
            if _looks_like_css(content):
                valid[name] = content
        elif lower.endswith(".js"):
            if _looks_like_js(content):
                valid[name] = content
        elif lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            continue
        elif is_code_listing(content):
            valid[name] = content
    return valid


def javascript_project_complete(files: dict[str, str]) -> bool:
    if not files:
        return False
    has_html = any(_looks_like_html(c) for n, c in files.items() if n.lower().endswith((".html", ".htm")))
    has_css = any(_looks_like_css(c) for n, c in files.items() if n.lower().endswith(".css"))
    has_js = any(_looks_like_js(c) for n, c in files.items() if n.lower().endswith(".js"))
    return has_html and has_css and has_js


def missing_web_parts(files: dict[str, str]) -> list[str]:
    missing: list[str] = []
    if not any(_looks_like_html(c) for n, c in files.items() if n.lower().endswith((".html", ".htm"))):
        missing.append("html/index.html")
    if not any(_looks_like_css(c) for n, c in files.items() if n.lower().endswith(".css")):
        missing.append("css/style.css")
    if not any(_looks_like_js(c) for n, c in files.items() if n.lower().endswith(".js")):
        missing.append("js/script.js")
    return missing


def is_javascript_language(language: str) -> bool:
    from backend.infrastructure.adapters.code_tools import is_web_toolkit

    return is_web_toolkit(language)


CODER_WEB_RETRY_NOTE = """
Предыдущий ответ отклонён: нужны ПОЛНЫЕ исходники, а не описание проекта или текст отчёта.
Верни JSON с реальным кодом:
- html/index.html — только интерфейс приложения (форма, кнопки), БЕЗ разделов «Цель работы», «Теоретические сведения», «Лабораторная работа»
- css/style.css — полные стили (Flexbox)
- js/script.js — валидация, localStorage, window.open / result.html
Не пиши текстовое описание, теорию и формулировку задания вместо кода.
"""
