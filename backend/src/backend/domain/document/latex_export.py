"""Pure builder: content_draft JSON → LaTeX (GOST-friendly basics)."""

from __future__ import annotations

import json
import re
from typing import Any

from backend.domain.document.draft_text import draft_to_plain_text


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    result = text
    for char, escaped in replacements.items():
        result = result.replace(char, escaped)
    return result


def _section(title: str, body: str) -> str:
    title = title.strip()
    body = body.strip()
    if not title and not body:
        return ""
    chunks = [f"\\section{{{_latex_escape(title)}}}" if title else ""]
    for paragraph in body.split("\n\n"):
        paragraph = paragraph.strip()
        if paragraph:
            chunks.append(_latex_escape(paragraph))
    return "\n\n".join(chunk for chunk in chunks if chunk)


def _coursework_sections(data: dict[str, Any]) -> str:
    parts: list[str] = []

    intro = data.get("intro") or []
    if intro:
        body = "\n\n".join(str(x) for x in intro if x)
        parts.append(_section("Введение", body))

    for section in data.get("sections") or []:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title") or "Раздел")
        paragraphs = section.get("paragraphs") or []
        body = "\n\n".join(str(x) for x in paragraphs if x)
        parts.append(_section(title, body))

    conclusion = data.get("conclusion") or []
    if conclusion:
        body = "\n\n".join(str(x) for x in conclusion if x)
        parts.append(_section("Заключение", body))

    sources = data.get("sources") or []
    if sources:
        body = "\n\n".join(str(x) for x in sources if x)
        parts.append(_section("Список литературы", body))

    return "\n\n".join(part for part in parts if part)


def _lab_sections(data: dict[str, Any]) -> str:
    mapping = [
        ("Цель работы", "purpose"),
        ("Теоретические сведения", "theory"),
        ("Задание варианта", "variant_task"),
        ("Исходный код программы", "program_code"),
        ("Работа программы", "program_work"),
        ("Выводы", "conclusions"),
    ]
    parts: list[str] = []
    for title, key in mapping:
        value = str(data.get(key) or "").strip()
        if not value:
            continue
        if key == "program_code":
            parts.append(
                f"\\section{{{title}}}\n\\begin{{verbatim}}\n{value}\n\\end{{verbatim}}"
            )
        else:
            parts.append(_section(title, value))
    return "\n\n".join(parts)


def build_latex_document(
    *,
    content_draft: str,
    work_type: str,
    title: str = "Курсовая работа",
    structure_outline: str = "",
) -> str:
    body = ""
    try:
        data = json.loads(content_draft or "{}")
        if isinstance(data, dict):
            body = _coursework_sections(data) if work_type == "coursework" else _lab_sections(data)
    except json.JSONDecodeError:
        body = _latex_escape(content_draft)

    if not body.strip():
        body = _latex_escape(draft_to_plain_text(content_draft, work_type=work_type))

    outline_block = ""
    if structure_outline.strip():
        outline_block = (
            "\\section*{План}\n"
            + _latex_escape(structure_outline.strip())
            + "\n\n"
        )

    safe_title = _latex_escape(re.sub(r"\s+", " ", title.strip()) or "Учебная работа")

    return f"""\\documentclass[14pt]{{extarticle}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T2A]{{fontenc}}
\\usepackage[russian]{{babel}}
\\usepackage{{times}}
\\usepackage{{geometry}}
\\geometry{{left=3cm,right=1.5cm,top=2cm,bottom=2cm}}
\\usepackage{{setspace}}
\\onehalfspacing
\\begin{{document}}
\\begin{{center}}
\\Large\\textbf{{{safe_title}}}
\\end{{center}}

{outline_block}{body}
\\end{{document}}
"""
