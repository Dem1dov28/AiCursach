"""Подготовка и дополнение контента лабораторной работы."""

from __future__ import annotations

import re
from typing import Any

from backend.infrastructure.adapters.text_utils import as_text, join_texts
from backend.infrastructure.adapters.lab_code import resolve_program_code, _block_looks_like_source, is_code_listing
from backend.infrastructure.adapters.source_sanitize import contains_lab_report_text
from backend.domain.workflow.variant_select import extract_individual_task


def _nonempty(value: Any) -> str:
    text = str(value or "").strip()
    return text


def _strip_html_markup(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _looks_like_ui_mockup(text: str) -> bool:
    sample = (text or "").strip().lower()
    if not sample:
        return False
    if any(tag in sample for tag in ("<form", "<input", "<button", "<select", "<textarea")):
        return True
    if re.search(r"<!doctype\s+html|<html[\s>]", sample):
        return True
    return False


def _resolve_variant_task(content: dict, state: dict) -> str:
    """Текст варианта из задания, без HTML-макетов от Writer."""
    from_assignment = as_text(state.get("variant_task_text")).strip()
    if from_assignment:
        return from_assignment[:5000]

    writer_text = _nonempty(content.get("variant_task"))
    if writer_text and not _looks_like_ui_mockup(writer_text):
        return _strip_html_markup(writer_text)[:5000]

    full = as_text(state.get("assignment_full_text")).strip()
    variant = as_text(state.get("assignment_variant")).strip()
    if full:
        individual = extract_individual_task(full, variant) or extract_individual_task(full, "")
        if individual:
            return individual[:5000]

    assignment = as_text(state.get("assignment_text")).strip()
    if assignment:
        return assignment[:5000]

    requirements = as_text(state.get("requirements")).strip()
    if requirements:
        return requirements[:3000]

    return "Выполнить задание согласно методическим указаниям."


def _clean_program_code(code: str) -> str:
    """Убрать бинарные/фиктивные файлы и текстовые описания из листинга."""
    if "// === " not in code:
        return code if is_code_listing(code) else ""
    parts: list[str] = []
    for block in re.split(r"(?=// === )", code):
        block = block.strip()
        if not block or not block.startswith("// === "):
            continue
        body = block.split("\n", 1)[1] if "\n" in block else ""
        lower = block.lower()
        if ".png ===" in lower or ".jpg ===" in lower:
            continue
        if "добавьте сюда" in lower and "изображение" in lower:
            continue
        if contains_lab_report_text(body):
            continue
        if not _block_looks_like_source(body):
            continue
        parts.append(block)
    return "\n\n".join(parts) if parts else ""


def enrich_lab_content(content: dict, state: dict) -> dict:
    """Заполнить пустые разделы из задания, анализа и исследования."""
    out = dict(content)
    topic = _nonempty(state.get("topic")) or "лабораторная работа"
    requirements = as_text(state.get("requirements")).strip()
    research = join_texts(state.get("research_findings") or [], sep="\n\n").strip()

    if not _nonempty(out.get("purpose")):
        out["purpose"] = (
            f"Цель работы — изучить тему «{topic}» и закрепить практические навыки "
            "в соответствии с методическими указаниями."
        )

    if not _nonempty(out.get("theory")):
        if research:
            out["theory"] = research[:6000]
        elif requirements:
            out["theory"] = requirements[:4000]
        else:
            out["theory"] = (
                f"Теоретические сведения по теме «{topic}». "
                "Раздел содержит основные понятия, используемые при выполнении задания."
            )

    out["variant_task"] = _resolve_variant_task(out, state)

    if not _nonempty(out.get("conclusions")):
        out["conclusions"] = (
            f"В ходе выполнения лабораторной работы по теме «{topic}» были изучены "
            "теоретические основы и выполнено практическое задание. "
            "Разработанное программное решение соответствует требованиям варианта."
        )

    if not _nonempty(out.get("program_work")):
        lang = state.get("code_language", "")
        if lang.lower() in ("javascript", "html", "js", "web"):
            out["program_work"] = (
                "Программа реализована в виде HTML-страницы с CSS и JavaScript. "
                "На рисунках ниже представлены экранные формы работы приложения."
            )
        else:
            out["program_work"] = "Результаты работы программы представлены ниже."

    code = resolve_program_code(
        out,
        state,
        str(state.get("project_name") or "WorkProject"),
    )
    if code:
        out["program_code"] = _clean_program_code(code)
    elif _nonempty(out.get("program_code")):
        out.pop("program_code", None)

    out["topic"] = topic
    return out
