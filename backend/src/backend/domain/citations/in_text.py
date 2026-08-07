"""In-text citation coverage and light ГОСТ checks for bibliography entries."""

from __future__ import annotations

import json
import re

from backend.domain.citations.validator import CitationIssue

_CITATION_RE = re.compile(r"\[(\d+)\]")
_YEAR_RE = re.compile(r"(?:19|20)\d{2}")
# Rough ГОСТ-like: starts with [N] or Author, has year somewhere.
_GOST_WEAK_RE = re.compile(
    r"^(\[\d+\]\s*)?[A-Za-zА-Яа-яЁё].{8,}(?:19|20)\d{2}",
    re.UNICODE,
)


def parse_draft_dict(content_draft: str) -> dict:
    try:
        data = json.loads(content_draft or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def body_text_for_citations(content_draft: str) -> str:
    """Text where in-text [N] should appear (exclude sources list itself)."""
    data = parse_draft_dict(content_draft)
    if not data:
        return content_draft or ""
    chunks: list[str] = []
    for key in ("intro", "purpose", "theory", "conclusion", "variant_task", "program_work"):
        val = data.get(key)
        if isinstance(val, list):
            chunks.extend(str(x) for x in val)
        elif isinstance(val, str):
            chunks.append(val)
    sections = data.get("sections") or []
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            chunks.append(str(section.get("title") or ""))
            paras = section.get("paragraphs") or []
            if isinstance(paras, list):
                chunks.extend(str(p) for p in paras)
    return "\n".join(chunks)


def collect_in_text_citation_numbers(content_draft: str) -> set[int]:
    return {int(m) for m in _CITATION_RE.findall(body_text_for_citations(content_draft))}


def source_count(content_draft: str) -> int:
    data = parse_draft_dict(content_draft)
    sources = data.get("sources") or []
    if not isinstance(sources, list):
        return 0
    return len([s for s in sources if str(s).strip()])


def validate_in_text_coverage(
    content_draft: str,
    *,
    min_citations: int = 3,
) -> list[CitationIssue]:
    """Require enough [N] markers in body and that sources are actually cited."""
    if not (content_draft or "").strip():
        return []

    n_sources = source_count(content_draft)
    if n_sources == 0:
        return [
            CitationIssue(
                citation="sources",
                reason="Список источников пуст",
            )
        ]

    cited = collect_in_text_citation_numbers(content_draft)
    issues: list[CitationIssue] = []
    if len(cited) < min_citations:
        issues.append(
            CitationIssue(
                citation="[N]",
                reason=(
                    f"В тексте мало ссылок на источники "
                    f"(найдено {len(cited)}, нужно ≥{min_citations})"
                ),
            )
        )

    known = set(range(1, n_sources + 1))
    unused = sorted(known - cited)
    if unused and len(unused) >= max(1, n_sources // 2):
        preview = ", ".join(f"[{n}]" for n in unused[:8])
        issues.append(
            CitationIssue(
                citation="sources",
                reason=f"Больше половины источников не упомянуты в тексте: {preview}",
            )
        )
    return issues


def validate_gost_ish_sources(content_draft: str) -> list[CitationIssue]:
    """Lightweight ГОСТ shape: author-like start + year; not a full ГОСТ 7.0.5 parser."""
    data = parse_draft_dict(content_draft)
    sources = data.get("sources") or []
    if not isinstance(sources, list):
        return []

    issues: list[CitationIssue] = []
    for index, item in enumerate(sources, start=1):
        text = str(item or "").strip()
        if not text:
            continue
        if not _YEAR_RE.search(text):
            issues.append(
                CitationIssue(
                    citation=f"[{index}]",
                    reason="В библиографической записи нет года издания",
                )
            )
            continue
        if not _GOST_WEAK_RE.search(text):
            issues.append(
                CitationIssue(
                    citation=f"[{index}]",
                    reason="Запись слабо похожа на ГОСТ (нужны автор/название и год)",
                )
            )
    return issues
