"""Writer coursework multipass with mocked LLM."""

from __future__ import annotations

import json
from unittest.mock import patch

from backend.infrastructure.langgraph.nodes.writer import writer_node


def _llm_side_effect(_llm, prompt: str) -> str:
    if "ТОЛЬКО введение" in prompt or "Напиши ТОЛЬКО введение" in prompt:
        return json.dumps({"intro": ["актуальность", "цель", "задачи"]}, ensure_ascii=False)
    if "ОДНУ главу" in prompt:
        # title embedded in prompt
        return json.dumps(
            {"title": "глава", "paragraphs": ["абзац1", "абзац2", "абзац3", "абзац4"]},
            ensure_ascii=False,
        )
    if "заключение, список источников" in prompt:
        return json.dumps(
            {
                "conclusion": ["вывод1", "вывод2"],
                "sources": [f"[{i}] Источник {i}" for i in range(1, 9)],
                "referat": {
                    "keywords": "А, Б",
                    "goal": "цель",
                    "methodology": "методы",
                    "results": "результаты",
                    "tech_stack": "стек",
                    "application": "область",
                },
            },
            ensure_ascii=False,
        )
    # revision / full single-pass
    return json.dumps(
        {
            "intro": ["i1", "i2", "i3"],
            "sections": [
                {"title": "1", "paragraphs": ["a", "b", "c", "d"]},
                {"title": "2", "paragraphs": ["a", "b", "c", "d"]},
                {"title": "3", "paragraphs": ["a", "b", "c", "d"]},
            ],
            "conclusion": ["c1", "c2"],
            "sources": [f"[{i}] s" for i in range(1, 9)],
        },
        ensure_ascii=False,
    )


def test_writer_coursework_multipass_builds_full_draft():
    with patch("backend.infrastructure.langgraph.nodes.writer.get_llm"), patch(
        "backend.infrastructure.langgraph.nodes.writer.llm_text",
        side_effect=_llm_side_effect,
    ):
        result = writer_node(
            {
                "work_type": "auto",
                "detected_work_kind": "coursework",
                "topic": "ИС склада",
                "requirements": "сделать курсовую",
                "structure_outline": "1. Анализ\n2. Проектирование\n3. Реализация",
                "content_draft": "",
                "critique_notes": "",
            }
        )

    draft = json.loads(result["content_draft"])
    assert len(draft["intro"]) >= 2
    assert len(draft["sections"]) == 3
    assert len(draft["conclusion"]) >= 2
    assert len(draft["sources"]) >= 5
    assert any("multi-pass" in line for line in result.get("tool_log") or [])
