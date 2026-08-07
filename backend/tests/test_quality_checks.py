"""Tests for academic quality checks."""

from backend.domain.citations.source_matcher import validate_sources_against_context
from backend.domain.quality.analyze_draft import analyze_draft_quality
from backend.domain.style.cliche_checker import find_cliches, validate_style


def test_find_cliches_detects_phrases():
    text = "В современном мире важно отметить, что в современном мире всё меняется."
    issues = find_cliches(text)
    phrases = {item.phrase for item in issues}
    assert "в современном мире" in phrases
    assert "важно отметить" in phrases


def test_validate_style_on_lab_draft():
    draft = '{"purpose": "В современном мире важно отметить актуальность."}'
    issues = validate_style(draft, work_type="lab")
    assert len(issues) >= 2


def test_source_matcher_flags_unknown_source():
    draft = '{"sources": ["Выдуманный А.А. Несуществующая книга 2099"]}'
    issues = validate_sources_against_context(
        draft,
        ["Методические указания кафедры программирования"],
    )
    assert len(issues) == 1


def test_analyze_draft_quality_combined():
    draft = (
        '{"sections": [{"title": "1", "paragraphs": ["В современном мире [1]"]}], '
        '"sources": ["Реальный учебник БГУИР 2020"]}'
    )
    result = analyze_draft_quality(
        draft,
        work_type="coursework",
        context_texts=["Реальный учебник БГУИР 2020 для студентов"],
    )
    assert result["style_issues"]
    assert isinstance(result["citation_issues"], list)
