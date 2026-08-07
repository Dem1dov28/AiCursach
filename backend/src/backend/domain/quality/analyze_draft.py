"""Aggregate draft quality checks (citations, sources, style)."""

from __future__ import annotations

from collections.abc import Callable

from backend.domain.citations.crossref_verify import verify_bibliography_dois
from backend.domain.citations.in_text import (
    validate_gost_ish_sources,
    validate_in_text_coverage,
)
from backend.domain.citations.source_matcher import (
    source_entries,
    validate_sources_against_context,
)
from backend.domain.citations.validator import validate_citations
from backend.domain.style.cliche_checker import validate_style


def analyze_draft_quality(
    content_draft: str,
    *,
    work_type: str = "lab",
    context_texts: list[str] | None = None,
    resolve_doi_title: Callable[[str], str | None] | None = None,
    verify_doi: bool | None = None,
    require_in_text_citations: bool | None = None,
) -> dict[str, list[dict[str, str | int]]]:
    citation_issues = [issue.to_dict() for issue in validate_citations(content_draft)]
    citation_issues.extend(
        issue.to_dict() for issue in validate_gost_ish_sources(content_draft)
    )

    need_in_text = (
        require_in_text_citations
        if require_in_text_citations is not None
        else work_type in ("coursework", "auto", "custom")
    )
    if need_in_text:
        citation_issues.extend(
            issue.to_dict()
            for issue in validate_in_text_coverage(content_draft, min_citations=3)
        )

    if context_texts:
        citation_issues.extend(
            issue.to_dict()
            for issue in validate_sources_against_context(content_draft, context_texts)
        )
    crossref_enabled = verify_doi if verify_doi is not None else bool(resolve_doi_title)
    if crossref_enabled and resolve_doi_title:
        entries = source_entries(content_draft)
        if entries:
            citation_issues.extend(
                issue.to_dict()
                for issue in verify_bibliography_dois(entries, resolve_title=resolve_doi_title)
            )
    style_issues = [issue.to_dict() for issue in validate_style(content_draft, work_type=work_type)]
    return {
        "citation_issues": citation_issues,
        "style_issues": style_issues,
    }
