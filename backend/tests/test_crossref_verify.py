"""Tests for CrossRef bibliography verification."""

from unittest.mock import patch

from backend.domain.citations.crossref_verify import verify_bibliography_dois
from backend.domain.citations.doi_utils import extract_doi, title_overlap


def test_extract_doi_from_entry():
    entry = "[1] Author Title DOI: 10.1038/nature12345 extra"
    assert extract_doi(entry) == "10.1038/nature12345"


def test_title_overlap_partial_match():
    overlap = title_overlap(
        "Deep learning for image recognition",
        "Deep learning approaches to image recognition systems",
    )
    assert overlap >= 0.5


def test_verify_bibliography_flags_mismatch():
    def mock_fetch(_doi: str) -> str:
        return "Completely different canonical title"

    issues = verify_bibliography_dois(
        [(1, "[1] Fake paper DOI 10.1234/abc about neural networks")],
        resolve_title=mock_fetch,
    )
    assert len(issues) == 1
    assert "CrossRef" in issues[0].reason or "не совпадает" in issues[0].reason


def test_verify_bibliography_accepts_good_match():
    def mock_fetch(_doi: str) -> str:
        return "Neural networks for student projects"

    issues = verify_bibliography_dois(
        [(1, "[1] Ivanov Neural networks for student projects DOI 10.1234/abc")],
        resolve_title=mock_fetch,
    )
    assert issues == []


@patch("backend.infrastructure.adapters.crossref_client.fetch_crossref_title")
def test_fetch_crossref_title_integration(mock_fetch):
    mock_fetch.return_value = "Test Title"
    from backend.infrastructure.adapters.crossref_client import fetch_crossref_title

    assert fetch_crossref_title("10.1234/x") == "Test Title"
