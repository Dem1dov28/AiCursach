"""Pure citation validation against draft sources list."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_CITATION_RE = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class CitationIssue:
    citation: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"citation": self.citation, "reason": self.reason}


def _extract_sources(content_draft: str) -> set[int]:
    try:
        data = json.loads(content_draft or "{}")
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, dict):
        return set()

    sources = data.get("sources") or []
    numbers: set[int] = set()
    if isinstance(sources, list):
        for index, item in enumerate(sources, start=1):
            if item:
                numbers.add(index)
    return numbers


def _collect_citation_numbers(content_draft: str) -> set[int]:
    try:
        raw = json.dumps(json.loads(content_draft), ensure_ascii=False)
    except json.JSONDecodeError:
        raw = content_draft
    return {int(match) for match in _CITATION_RE.findall(raw)}


def validate_citations(content_draft: str) -> list[CitationIssue]:
    """Return issues for [N] markers that are missing from sources."""
    if not content_draft.strip():
        return []

    known = _extract_sources(content_draft)
    if not known:
        return []

    issues: list[CitationIssue] = []
    for number in sorted(_collect_citation_numbers(content_draft)):
        if number not in known:
            issues.append(
                CitationIssue(
                    citation=f"[{number}]",
                    reason="Ссылка не найдена в списке источников",
                )
            )
    return issues
