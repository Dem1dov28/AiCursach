"""Tests for LLM-driven agent clarification."""

from backend.domain.workflow.clarification import (
    parse_llm_clarification,
    resolve_clarification,
    should_request_clarification,
)


def test_parse_llm_clarification_explicit():
    clar, conf, explicit = parse_llm_clarification(
        {
            "confidence": 0.55,
            "needs_clarification": True,
            "clarification": {
                "scenario": "ambiguous_task",
                "question": "Какой вариант задания выполнять?",
                "options": ["Вариант А", "Вариант Б"],
            },
        }
    )
    assert explicit is True
    assert clar is not None
    assert clar["question"].startswith("Какой")
    assert conf == 0.55


def test_should_request_interactive_on_explicit_doubt():
    state = {"autonomy_level": "interactive", "confidence_threshold": 0.8}
    assert should_request_clarification(
        state,
        agent="writer",
        confidence=0.95,
        clarification={"question": "Q?", "options": ["A"]},
        explicit_request=True,
    )


def test_should_not_request_full_auto():
    state = {"autonomy_level": "full_auto"}
    assert not should_request_clarification(
        state,
        agent="writer",
        confidence=0.2,
        clarification={"question": "Q?", "options": ["A"]},
        explicit_request=True,
    )


def test_interactive_does_not_pause_without_question():
    state = {"autonomy_level": "interactive"}
    for agent in ("writer", "coder_gen", "bibliography_verifier"):
        assert not should_request_clarification(
            state,
            agent=agent,
            confidence=0.99,
            clarification=None,
        )


def test_resolve_prefers_explicit_llm():
    clar, conf, explicit = resolve_clarification(
        {},
        {
            "needs_clarification": True,
            "confidence": 0.9,
            "clarification": {
                "question": "Уточните тему",
                "options": ["A", "B"],
            },
        },
        heuristic=lambda s, d: ({"question": "Heuristic?", "options": ["X"]}, 0.5),
    )
    assert explicit is True
    assert clar is not None
    assert "Уточните" in clar["question"]
