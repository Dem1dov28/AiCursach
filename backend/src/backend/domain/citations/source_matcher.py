"""Cross-check bibliography entries against uploaded context texts."""

from __future__ import annotations

import json
import re

from backend.domain.citations.validator import CitationIssue

_AUTHOR_RE = re.compile(r"^([A-Za-zА-Яа-яЁё\-]+)")


def source_entries(content_draft: str) -> list[tuple[int, str]]:
    return _source_entries(content_draft)


def _source_entries(content_draft: str) -> list[tuple[int, str]]:
    try:
        data = json.loads(content_draft or "{}")
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []

    sources = data.get("sources") or []
    entries: list[tuple[int, str]] = []
    if isinstance(sources, list):
        for index, item in enumerate(sources, start=1):
            text = str(item or "").strip()
            if text:
                entries.append((index, text))
    return entries


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _tokens_for_match(text: str) -> set[str]:
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9\-]{4,}", text.lower())
    return {word for word in words if len(word) >= 4}


def _source_supported(entry: str, context_text: str) -> bool:
    entry_norm = _normalize(entry)
    context_norm = _normalize(context_text)
    if not entry_norm or not context_norm:
        return False

    if entry_norm in context_norm:
        return True

    author_match = _AUTHOR_RE.match(entry.strip())
    if author_match:
        author = author_match.group(1).lower()
        if len(author) >= 4 and author in context_norm:
            return True

    entry_tokens = _tokens_for_match(entry)
    if not entry_tokens:
        return False
    context_tokens = _tokens_for_match(context_text)
    overlap = entry_tokens & context_tokens
    return len(overlap) >= max(2, len(entry_tokens) // 3)


def validate_sources_against_context(
    content_draft: str,
    context_texts: list[str],
) -> list[CitationIssue]:
    """Flag bibliography items that do not overlap uploaded materials."""
    combined = "\n".join(text for text in context_texts if text.strip()).strip()
    if not combined:
        return []

    issues: list[CitationIssue] = []
    for index, entry in _source_entries(content_draft):
        if _source_supported(entry, combined):
            continue
        preview = entry[:80] + ("…" if len(entry) > 80 else "")
        issues.append(
            CitationIssue(
                citation=f"[источник {index}]",
                reason=f"Не подтверждён загруженными материалами: {preview}",
            )
        )
    return issues
