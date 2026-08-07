"""Tests for bibliography verifier node (validation path, no LLM)."""

from backend.infrastructure.langgraph.nodes.bibliography_verifier import bibliography_verifier_node


def test_bibliography_verifier_clean_draft():
    draft = (
        '{"intro": ["Актуальность [1].", "Цель [2].", "Задачи [3]."], '
        '"sections": [{"title": "1", "paragraphs": ["анализ [1]", "ещё [2]", "и [3]"]}], '
        '"conclusion": ["вывод"], '
        '"sources": ['
        '"[1] Иванов И.И. Учебник. — Минск: БГУИР, 2020.", '
        '"[2] Петров П.П. Статья. — 2021.", '
        '"[3] Сидоров С.С. Монография. — 2019."]}'
    )
    result = bibliography_verifier_node(
        {
            "content_draft": draft,
            "work_type": "coursework",
            "detected_work_kind": "coursework",
            "methodical_text": "Иванов И.И. Учебник. — Минск: БГУИР, 2020. Петров П.П. Статья. Сидоров С.С. Монография.",
            "research_findings": [
                "[1] Иванов И.И. Учебник. — Минск: БГУИР, 2020.",
                "[2] Петров П.П. Статья. — 2021.",
                "[3] Сидоров С.С. Монография. — 2019.",
            ],
        }
    )
    assert result["bibliography_verified"] is True
    assert result["citation_issues"] == []


def test_bibliography_verifier_disabled():
    result = bibliography_verifier_node(
        {
            "content_draft": '{"sources": ["bad"]}',
            "work_type": "auto",
            "enable_bibliography_verifier": False,
        }
    )
    assert result["bibliography_verified"] is True
    assert "отключена" in result["tool_log"][0].lower()
