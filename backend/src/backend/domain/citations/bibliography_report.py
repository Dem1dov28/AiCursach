"""Structured bibliography audit report (BibGuard-style summary)."""

from __future__ import annotations

import json
import re
from typing import Any

from collections.abc import Callable

from backend.domain.citations.doi_utils import extract_doi, title_overlap
from backend.domain.citations.source_matcher import source_entries
from backend.domain.quality.analyze_draft import analyze_draft_quality

_CITATION_RE = re.compile(r"\[(\d+)\]")


def _citations_in_text(content_draft: str) -> set[int]:
    try:
        raw = json.dumps(json.loads(content_draft), ensure_ascii=False)
    except json.JSONDecodeError:
        raw = content_draft
    return {int(match) for match in _CITATION_RE.findall(raw)}


def _doi_status(
    entry: str,
    *,
    verify: bool,
    resolve_title: Callable[[str], str | None] | None,
) -> str:
    doi = extract_doi(entry)
    if not doi:
        return "missing"
    if not verify:
        return "present"
    if resolve_title is None:
        return "present"
    canonical = resolve_title(doi)
    if not canonical:
        return "invalid"
    if title_overlap(entry, canonical) < 0.35:
        return "mismatch"
    return "ok"


def _score_from_counts(
    *,
    total_sources: int,
    orphan_citations: int,
    doi_failed: int,
    context_issues: int,
    citation_issues: int,
) -> int:
    if total_sources == 0 and citation_issues == 0:
        return 100
    penalty = orphan_citations * 15 + doi_failed * 10 + context_issues * 8 + max(0, citation_issues - orphan_citations - doi_failed - context_issues) * 5
    return max(0, min(100, 100 - penalty))


def build_bibliography_report(
    content_draft: str,
    *,
    work_type: str = "auto",
    context_texts: list[str] | None = None,
    verify_doi: bool | None = None,
    resolve_doi_title: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
    """Build HTML-friendly structured bibliography audit."""
    verify = verify_doi if verify_doi is not None else bool(resolve_doi_title)
    entries = source_entries(content_draft)
    cited = _citations_in_text(content_draft)
    quality = analyze_draft_quality(
        content_draft,
        work_type=work_type,
        context_texts=context_texts,
        resolve_doi_title=resolve_doi_title if verify else None,
        verify_doi=verify,
    )
    all_issues = quality.get("citation_issues") or []

    issues_by_category: dict[str, list[dict[str, str]]] = {
        "citation": [],
        "doi": [],
        "context": [],
        "other": [],
    }
    for issue in all_issues:
        reason = str(issue.get("reason") or "")
        if "CrossRef" in reason or "DOI" in reason:
            issues_by_category["doi"].append(issue)
        elif "материал" in reason.lower() or "контекст" in reason.lower() or "загружен" in reason.lower():
            issues_by_category["context"].append(issue)
        elif "списк" in reason.lower() or "ссылка" in reason.lower():
            issues_by_category["citation"].append(issue)
        else:
            issues_by_category["other"].append(issue)

    sources: list[dict[str, Any]] = []
    doi_ok = doi_failed = 0
    for index, text in entries:
        status = _doi_status(text, verify=verify, resolve_title=resolve_doi_title)
        if status == "ok":
            doi_ok += 1
        elif status in ("invalid", "mismatch"):
            doi_failed += 1
        entry_issues = [
            issue
            for issue in all_issues
            if f"[источник {index}]" in str(issue.get("citation") or "")
            or f"[{index}]" in str(issue.get("citation") or "")
        ]
        sources.append(
            {
                "index": index,
                "text": text,
                "doi": extract_doi(text) or "",
                "doi_status": status,
                "cited_in_text": index in cited,
                "issues": entry_issues,
            }
        )

    orphan = len([n for n in cited if n not in {idx for idx, _ in entries}])
    summary = {
        "total_sources": len(entries),
        "citations_in_text": len(cited),
        "orphan_citations": orphan,
        "doi_verified": doi_ok,
        "doi_failed": doi_failed,
        "issues_total": len(all_issues),
        "score": _score_from_counts(
            total_sources=len(entries),
            orphan_citations=orphan,
            doi_failed=doi_failed,
            context_issues=len(issues_by_category["context"]),
            citation_issues=len(all_issues),
        ),
    }

    return {
        "summary": summary,
        "sources": sources,
        "issues_by_category": issues_by_category,
        "citation_issues": all_issues,
    }


def context_texts_from_state(state: dict[str, Any]) -> list[str]:
    texts = [
        state.get("methodical_text") or "",
        state.get("assignment_text") or "",
        state.get("general_requirements_text") or "",
    ]
    texts.extend(state.get("research_findings") or [])
    return [text for text in texts if str(text).strip()]


def render_bibliography_report_html(report: dict[str, Any], *, title: str = "Отчёт по библиографии") -> str:
    """Standalone HTML report for ZIP export."""
    summary = report.get("summary") or {}
    sources = report.get("sources") or []
    categories = report.get("issues_by_category") or {}
    score = int(summary.get("score") or 0)
    score_color = "#2d8a4e" if score >= 80 else "#b8860b" if score >= 50 else "#c0392b"

    source_rows = []
    for item in sources:
        flags = []
        if not item.get("cited_in_text"):
            flags.append("не цитируется")
        doi_status = str(item.get("doi_status") or "")
        if doi_status in ("invalid", "mismatch"):
            flags.append(f"DOI: {doi_status}")
        issue_lines = "".join(
            f"<li>{issue.get('reason', '')}</li>"
            for issue in (item.get("issues") or [])
        )
        source_rows.append(
            f"<tr><td>[{item.get('index')}]</td>"
            f"<td>{_html_escape(str(item.get('text') or ''))}</td>"
            f"<td>{doi_status or '—'}</td>"
            f"<td>{', '.join(flags) or '—'}</td>"
            f"<td><ul>{issue_lines}</ul></td></tr>"
        )

    category_blocks = []
    labels = {
        "citation": "Ссылки [N]",
        "doi": "DOI / CrossRef",
        "context": "Соответствие материалам",
        "other": "Прочее",
    }
    for key, label in labels.items():
        items = categories.get(key) or []
        if not items:
            continue
        rows = "".join(
            f"<li><strong>{_html_escape(str(i.get('citation') or ''))}</strong> — "
            f"{_html_escape(str(i.get('reason') or ''))}</li>"
            for i in items
        )
        category_blocks.append(f"<h3>{label}</h3><ul>{rows}</ul>")

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<title>{_html_escape(title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
h1 {{ margin-bottom: 0.25rem; }}
.score {{ font-size: 2rem; font-weight: 700; color: {score_color}; }}
.stats {{ display: flex; gap: 1.5rem; margin: 1rem 0; flex-wrap: wrap; }}
.stats div {{ background: #f4f4f4; padding: 0.5rem 0.75rem; border-radius: 6px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; font-size: 0.9rem; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem; vertical-align: top; }}
th {{ background: #eee; text-align: left; }}
ul {{ margin: 0.25rem 0 0 1rem; padding: 0; }}
</style>
</head>
<body>
<h1>{_html_escape(title)}</h1>
<p class="score">Score: {score}/100</p>
<div class="stats">
  <div><strong>{summary.get('total_sources', 0)}</strong><br/>источников</div>
  <div><strong>{summary.get('citations_in_text', 0)}</strong><br/>ссылок в тексте</div>
  <div><strong>{summary.get('doi_verified', 0)}</strong><br/>DOI OK</div>
  <div><strong>{summary.get('issues_total', 0)}</strong><br/>замечаний</div>
</div>
<h2>Источники</h2>
<table>
<thead><tr><th>#</th><th>Запись</th><th>DOI</th><th>Флаги</th><th>Замечания</th></tr></thead>
<tbody>{''.join(source_rows) if source_rows else '<tr><td colspan="5">Нет источников</td></tr>'}</tbody>
</table>
{''.join(category_blocks)}
</body>
</html>"""


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

