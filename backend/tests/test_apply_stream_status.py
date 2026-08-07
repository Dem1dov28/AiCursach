"""Unit tests for applyStreamEvent reducer (mirrors frontend logic)."""

from __future__ import annotations


def _apply_status(prev: dict, status: str) -> dict:
    """Python mirror of applyStreamEvent 'status' branch for regression tests."""
    patch = prev.get("statePatch") or {}
    paused = status == "paused"
    return {
        **prev,
        "awaitingPlanApproval": paused
        and bool(patch.get("awaiting_plan_approval"))
        and not patch.get("awaiting_clarification"),
        "awaitingClarification": paused and bool(patch.get("awaiting_clarification")),
    }


def test_status_paused_clarification_not_plan():
    prev = {
        "statePatch": {
            "awaiting_clarification": True,
            "awaiting_plan_approval": False,
        },
        "awaitingPlanApproval": False,
        "awaitingClarification": False,
    }
    next_state = _apply_status(prev, "paused")
    assert next_state["awaitingClarification"] is True
    assert next_state["awaitingPlanApproval"] is False


def test_status_paused_plan_not_clarification():
    prev = {
        "statePatch": {
            "awaiting_plan_approval": True,
            "awaiting_clarification": False,
        },
    }
    next_state = _apply_status(prev, "paused")
    assert next_state["awaitingPlanApproval"] is True
    assert next_state["awaitingClarification"] is False


def test_status_running_clears_hitl():
    prev = {
        "statePatch": {"awaiting_plan_approval": True},
        "awaitingPlanApproval": True,
        "awaitingClarification": True,
    }
    next_state = _apply_status(prev, "running")
    assert next_state["awaitingPlanApproval"] is False
    assert next_state["awaitingClarification"] is False
