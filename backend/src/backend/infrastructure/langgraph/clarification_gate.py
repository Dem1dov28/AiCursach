"""LangGraph interrupt gate for agent clarification."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.domain.workflow.clarification import (
    apply_clarification_answer,
    build_interrupt_payload,
    resolve_clarification,
    should_request_clarification,
)
from backend.domain.workflow.work_state import WorkState


def maybe_request_clarification(
    state: WorkState,
    *,
    agent: str,
    confidence: float,
    clarification: dict[str, Any] | None,
    explicit_request: bool = False,
) -> dict[str, Any]:
    """Pause graph and ask user when autonomy rules require it."""
    if not should_request_clarification(
        state,
        agent=agent,
        confidence=confidence,
        clarification=clarification,
        explicit_request=explicit_request,
    ):
        return {}

    if not clarification:
        return {}

    interrupt_payload = build_interrupt_payload(
        agent=agent,
        clarification=clarification,
        confidence=confidence,
    )

    from langgraph.types import interrupt

    user_answer = interrupt(interrupt_payload)
    merged = apply_clarification_answer(
        state,
        agent=agent,
        clarification=clarification,
        answer=user_answer,
    )
    merged["agent_confidence"] = confidence
    return merged


def gate_after_llm(
    state: WorkState,
    agent: str,
    llm_data: dict[str, Any] | None,
    heuristic: Callable[[dict[str, Any], dict[str, Any]], tuple[dict[str, Any] | None, float]]
    | None = None,
) -> dict[str, Any]:
    """Run clarification gate using LLM confidence + optional heuristic detector."""
    clarification, confidence, explicit = resolve_clarification(state, llm_data, heuristic)
    return maybe_request_clarification(
        state,
        agent=agent,
        confidence=confidence,
        clarification=clarification,
        explicit_request=explicit,
    )
