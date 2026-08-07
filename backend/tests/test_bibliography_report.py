"""Tests for bibliography audit report."""

import json

from backend.domain.citations.bibliography_report import (
    build_bibliography_report,
    render_bibliography_report_html,
)


def test_bibliography_report_empty_draft():
    report = build_bibliography_report("", verify_doi=False)
    assert report["summary"]["score"] == 100
    assert report["sources"] == []


def test_bibliography_report_with_sources_and_citation():
    draft = json.dumps(
        {
            "title": "Тест",
            "sections": [{"heading": "Введение", "body": "Текст [1] и [2]."}],
            "sources": [
                "Иванов И.И. Экономика — 2020.",
                "Петров П.П. Менеджмент DOI: 10.1234/example — 2021.",
            ],
        },
        ensure_ascii=False,
    )
    report = build_bibliography_report(draft, verify_doi=False)
    assert report["summary"]["total_sources"] == 2
    assert report["summary"]["citations_in_text"] == 2
    assert len(report["sources"]) == 2
    assert report["sources"][1]["doi_status"] == "present"


def test_bibliography_report_orphan_citation():
    draft = json.dumps(
        {
            "sections": [{"body": "Ссылка [3] без источника."}],
            "sources": ["Иванов — 2020."],
        },
        ensure_ascii=False,
    )
    report = build_bibliography_report(draft, verify_doi=False)
    assert report["summary"]["orphan_citations"] == 1
    assert report["summary"]["score"] < 100


def test_render_bibliography_report_html():
    report = build_bibliography_report(
        '{"sources": ["Иванов — 2020"], "sections": [{"body": "текст [1]"}]}',
        verify_doi=False,
    )
    html = render_bibliography_report_html(report, title="Test Report")
    assert "<html" in html
    assert "Test Report" in html
    assert "Score:" in html
