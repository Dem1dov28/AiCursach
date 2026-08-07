"""Verify bibliography DOIs against canonical metadata (pure domain logic)."""

from __future__ import annotations

from collections.abc import Callable

from backend.domain.citations.doi_utils import extract_doi, title_overlap
from backend.domain.citations.validator import CitationIssue


def verify_bibliography_dois(
    entries: list[tuple[int, str]],
    *,
    resolve_title: Callable[[str], str | None],
) -> list[CitationIssue]:
    """Flag entries where DOI exists but title does not match CrossRef record."""
    issues: list[CitationIssue] = []
    for index, entry in entries:
        doi = extract_doi(entry)
        if not doi:
            continue
        canonical = resolve_title(doi)
        if not canonical:
            issues.append(
                CitationIssue(
                    citation=f"[источник {index}]",
                    reason=f"DOI {doi} не найден в CrossRef — проверьте ссылку",
                )
            )
            continue
        overlap = title_overlap(entry, canonical)
        if overlap < 0.35:
            preview = canonical[:70] + ("…" if len(canonical) > 70 else "")
            issues.append(
                CitationIssue(
                    citation=f"[источник {index}]",
                    reason=f"DOI {doi}: заголовок не совпадает с CrossRef («{preview}»)",
                )
            )
    return issues
