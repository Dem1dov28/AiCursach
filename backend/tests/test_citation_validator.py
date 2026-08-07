"""Tests for citation domain validator."""

from backend.domain.citations.validator import validate_citations


def test_validate_citations_flags_unknown_reference():
    draft = """
    {
      "sections": [{"title": "1", "paragraphs": ["текст [2]"]}],
      "sources": ["[1] Книга"]
    }
    """
    issues = validate_citations(draft)
    assert len(issues) == 1
    assert issues[0].citation == "[2]"
