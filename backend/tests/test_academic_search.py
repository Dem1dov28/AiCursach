"""Tests for academic search adapter."""

from backend.infrastructure.adapters.academic_search import (
    AcademicHit,
    _dedupe_hits,
    _normalize_title,
    format_hits_for_researcher,
    search_russian_web_sources,
)


def test_dedupe_hits_by_title():
    hits = [
        AcademicHit("Alpha", "A", "2020", "", "u1", 1, "openalex", ""),
        AcademicHit("Alpha.", "B", "2021", "", "u2", 2, "openalex", ""),
    ]
    unique = _dedupe_hits(hits)
    assert len(unique) == 1


def test_format_hits_for_researcher():
    text = format_hits_for_researcher(
        [
            AcademicHit(
                title="Экономика предприятия",
                authors="Иванов И.И.",
                year="2023",
                doi="10.1234/test",
                url="https://example.org",
                cited_by=10,
                source="openalex",
                snippet="Краткое описание",
            )
        ]
    )
    assert "OpenAlex" in text
    assert "10.1234/test" in text
    assert _normalize_title("Test — Title!") == "test title"


def test_search_russian_web_sources_query():
    query = search_russian_web_sources("Экономика предприятия", "economics")
    assert "cyberleninka" in query
    assert "Экономика" in query
