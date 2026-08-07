"""Critiquer: no rubber-stamp on thin drafts."""

import json

from backend.infrastructure.langgraph.nodes.critiquer import critiquer_node


def _para(extra: str = "") -> str:
    return (
        "абзац текста курсовой работы достаточной длины для domain guard. " * 3 + extra
    ).strip()


def test_critiquer_rejects_short_lab_draft():
    result = critiquer_node(
        {
            "work_type": "lab",
            "content_draft": "коротко",
            "revision_number": 0,
            "max_revisions": 3,
        }
    )
    assert result["critique_rerun"] == "writer"
    assert "APPROVED" not in result["critique_notes"]


def test_critiquer_rejects_thin_coursework_auto():
    thin = (
        '{"intro":["x"],"sections":[{"title":"1","paragraphs":["a"]}],'
        '"conclusion":["y"],"sources":["[1] z"]}'
    )
    result = critiquer_node(
        {
            "work_type": "auto",
            "detected_work_kind": "coursework",
            "content_draft": thin,
            "revision_number": 0,
            "max_revisions": 3,
        }
    )
    assert result["critique_rerun"] == "writer"
    assert "неполн" in result["critique_notes"].lower() or "глав" in result["critique_notes"].lower()


def test_critiquer_routes_citation_gaps_to_bibliography():
    # Structure + volume OK, but no in-text citations → bibliography
    para = _para()
    draft = {
        "intro": [para, para, para],
        "sections": [
            {"title": "1 АНАЛИЗ", "paragraphs": [para, para, para, para]},
            {"title": "2 МЕТОДЫ И СРЕДСТВА", "paragraphs": [para, para, para, para]},
            {"title": "3 РЕАЛИЗ", "paragraphs": [para, para, para, para]},
        ],
        "conclusion": [para, para],
        "sources": [
            f"[{n}] Author {n}. Book. — Минск: БГУИР, 202{n % 10}." for n in range(1, 9)
        ],
    }

    result = critiquer_node(
        {
            "work_type": "coursework",
            "detected_work_kind": "coursework",
            "content_draft": json.dumps(draft, ensure_ascii=False),
            "revision_number": 0,
            "max_revisions": 3,
        }
    )
    assert result["critique_rerun"] == "bibliography_verifier"


def test_critiquer_finalizes_thin_with_warnings_at_limit():
    result = critiquer_node(
        {
            "work_type": "coursework",
            "detected_work_kind": "coursework",
            "content_draft": '{"intro":["x"],"sections":[],"sources":[]}',
            "revision_number": 3,
            "max_revisions": 3,
        }
    )
    assert result["critique_rerun"] == ""
    assert "FINALIZED" in result["critique_notes"]
    assert "APPROVED" not in result["critique_notes"]
