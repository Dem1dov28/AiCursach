"""Coursework draft structure helpers (pure domain, no I/O)."""

from __future__ import annotations

import json
import re
from typing import Any

from backend.domain.citations.in_text import validate_in_text_coverage


# Floors aligned with WRITER_COURSEWORK_PROMPT / multipass prompts (lower bounds).
MIN_INTRO_PARAS = 3
MIN_SECTIONS = 3
MIN_SECTION_PARAS = 4
MIN_CONCLUSION_PARAS = 2
MIN_SOURCES = 8
MIN_PARAGRAPH_CHARS = 80
MIN_BODY_CHARS = 3000
MIN_COURSEWORK_DRAFT_CHARS = 3500
MAX_MULTIPASS_SECTIONS = 5


def _count_substantial_paras(items: Any, *, min_chars: int = MIN_PARAGRAPH_CHARS) -> int:
    if not isinstance(items, list):
        return 0
    return sum(1 for p in items if len(str(p).strip()) >= min_chars)


def draft_body_char_count(data: dict[str, Any]) -> int:
    """Count prose characters in intro / sections / conclusion (not JSON/sources)."""
    total = 0
    for p in data.get("intro") or []:
        total += len(str(p).strip())
    for section in data.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for p in section.get("paragraphs") or []:
            total += len(str(p).strip())
    for p in data.get("conclusion") or []:
        total += len(str(p).strip())
    return total


def parse_coursework_draft(raw: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}
    return data if isinstance(data, dict) else {"raw_text": text}


def outline_titles_from_structure(
    structure_outline: str,
    *,
    fallback: int = 3,
    discipline: str | None = None,
) -> list[str]:
    """Extract chapter titles from planner outline text."""
    from backend.domain.document.discipline_outline import default_chapter_titles

    titles: list[str] = []
    for line in (structure_outline or "").splitlines():
        cleaned = line.strip().lstrip("-•*").strip()
        if not cleaned:
            continue
        # Prefer numbered chapters / uppercase section headers
        if re.match(r"^\d+[\.\)]\s*\S", cleaned) or re.match(r"^[1-9]\s+[А-ЯA-Z]", cleaned):
            titles.append(cleaned[:120])
        elif cleaned.isupper() and len(cleaned) > 8:
            titles.append(cleaned[:120])
        elif re.match(r"^(глава|раздел|section)\b", cleaned, re.I):
            titles.append(cleaned[:120])
    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for title in titles:
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(title)
    unique = unique[:MAX_MULTIPASS_SECTIONS]
    if len(unique) >= 2:
        return unique
    return default_chapter_titles(discipline, max_chapters=max(fallback, 3))[:MAX_MULTIPASS_SECTIONS]


def coursework_draft_issues(
    draft: dict[str, Any] | str | None,
    *,
    work_brief: dict[str, Any] | str | None = None,
    methodical_text: str = "",
) -> list[str]:
    """Return human-readable completeness issues for a coursework JSON draft.

    Volume floors come from work_brief / methodical when present; else defaults.
    """
    from backend.domain.document.work_brief import merge_volume_targets, required_sections_from_brief

    targets = merge_volume_targets(work_brief, methodical_text=methodical_text)
    min_intro = int(targets.get("min_intro_paras") or MIN_INTRO_PARAS)
    min_sections = MIN_SECTIONS
    min_section_paras = int(targets.get("min_section_paras") or MIN_SECTION_PARAS)
    min_conclusion = MIN_CONCLUSION_PARAS
    min_sources = int(targets.get("min_sources") or MIN_SOURCES)
    min_body = int(targets.get("min_body_chars") or MIN_BODY_CHARS)

    data = parse_coursework_draft(draft)
    issues: list[str] = []
    if data.get("raw_text") and not data.get("sections"):
        issues.append("черновик не в формате JSON курсовой (intro/sections/conclusion)")
        return issues

    intro = data.get("intro") or []
    if _count_substantial_paras(intro) < min_intro:
        issues.append(
            f"введение слишком короткое "
            f"(нужно ≥{min_intro} абзацев ≥{MIN_PARAGRAPH_CHARS} симв.)"
        )

    sections = data.get("sections") or []
    if not isinstance(sections, list) or len(sections) < min_sections:
        issues.append(f"мало глав (нужно ≥{min_sections})")
    else:
        thin = 0
        for section in sections:
            if not isinstance(section, dict):
                thin += 1
                continue
            paras = section.get("paragraphs") or []
            if _count_substantial_paras(paras) < min_section_paras:
                thin += 1
        if thin:
            issues.append(
                f"у {thin} глав недостаточно абзацев "
                f"(нужно ≥{min_section_paras} абз. ≥{MIN_PARAGRAPH_CHARS} симв.)"
            )

    conclusion = data.get("conclusion") or []
    if _count_substantial_paras(conclusion) < min_conclusion:
        issues.append(
            f"заключение слишком короткое "
            f"(нужно ≥{min_conclusion} абзацев ≥{MIN_PARAGRAPH_CHARS} симв.)"
        )

    sources = data.get("sources") or []
    if not isinstance(sources, list) or len([s for s in sources if str(s).strip()]) < min_sources:
        issues.append(f"мало источников (нужно ≥{min_sources})")

    from backend.domain.document.discipline_outline import draft_has_methods_chapter

    if isinstance(sections, list) and len(sections) >= min_sections and not draft_has_methods_chapter(data):
        issues.append("нет главы о методах / методике исследования")

    # Required section titles from GOST/methodical brief
    required = required_sections_from_brief(work_brief)
    if required and isinstance(sections, list):
        titles_blob = " ".join(
            str(s.get("title") or "") for s in sections if isinstance(s, dict)
        ).lower()
        intro_ok = _count_substantial_paras(intro) > 0
        concl_ok = _count_substantial_paras(conclusion) > 0
        for req in required:
            key = str(req).lower()
            if "введен" in key and not intro_ok:
                issues.append(f"нет обязательного раздела из методички: {req}")
            elif "заключен" in key and not concl_ok:
                issues.append(f"нет обязательного раздела из методички: {req}")
            elif "список" in key or "источник" in key:
                continue  # checked via sources count
            elif key and key not in titles_blob and "введен" not in key and "заключен" not in key:
                # soft: only flag if looks like a chapter name
                if any(ch.isdigit() for ch in key) or len(key) > 8:
                    if not any(key[:12] in str(s.get("title") or "").lower() for s in sections if isinstance(s, dict)):
                        issues.append(f"в плане/черновике нет раздела из методички: {req}")

    # In-text [N] coverage (P3 stage 1)
    raw_blob = draft if isinstance(draft, str) else json.dumps(data, ensure_ascii=False)
    for issue in validate_in_text_coverage(raw_blob, min_citations=3):
        issues.append(issue.reason)

    body_chars = draft_body_char_count(data)
    if body_chars < min_body:
        issues.append(f"объём основного текста мал (<{min_body} символов, сейчас {body_chars})")

    blob = json.dumps(data, ensure_ascii=False)
    if len(blob) < MIN_COURSEWORK_DRAFT_CHARS and min_body <= MIN_BODY_CHARS:
        issues.append(f"общий объём черновика мал (<{MIN_COURSEWORK_DRAFT_CHARS} символов JSON)")

    return issues

def merge_coursework_parts(
    *,
    intro: list[str] | None = None,
    sections: list[dict[str, Any]] | None = None,
    conclusion: list[str] | None = None,
    sources: list[str] | None = None,
    referat: dict[str, Any] | None = None,
    base: dict[str, Any] | None = None,
) -> dict[str, Any]:
    draft = dict(base or {})
    if intro is not None:
        draft["intro"] = [str(p).strip() for p in intro if str(p).strip()]
    if sections is not None:
        draft["sections"] = sections
    if conclusion is not None:
        draft["conclusion"] = [str(p).strip() for p in conclusion if str(p).strip()]
    if sources is not None:
        draft["sources"] = [str(s).strip() for s in sources if str(s).strip()]
    if referat is not None and isinstance(referat, dict):
        draft["referat"] = referat
    return draft
