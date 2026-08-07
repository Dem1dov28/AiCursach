"""In-text citation coverage and ГОСТ-ish source checks."""

from backend.domain.citations.in_text import (
    collect_in_text_citation_numbers,
    validate_gost_ish_sources,
    validate_in_text_coverage,
)


def test_collect_in_text_ignores_sources_list():
    draft = (
        '{"intro": ["Текст [1] и [2]."], '
        '"sources": ["[1] A 2020", "[2] B 2021", "[3] C 2022"]}'
    )
    assert collect_in_text_citation_numbers(draft) == {1, 2}


def test_validate_in_text_coverage_requires_minimum():
    draft = (
        '{"intro": ["Без ссылок."], '
        '"sections": [{"title": "1", "paragraphs": ["только [1]"]}], '
        '"sources": ["[1] A 2020", "[2] B 2021", "[3] C 2022", "[4] D 2023", "[5] E 2024"]}'
    )
    issues = validate_in_text_coverage(draft, min_citations=3)
    assert any("мало ссылок" in i.reason for i in issues)


def test_validate_gost_ish_requires_year():
    draft = '{"sources": ["[1] Автор. Книга без года."]}'
    issues = validate_gost_ish_sources(draft)
    assert issues
    assert "года" in issues[0].reason.lower()
