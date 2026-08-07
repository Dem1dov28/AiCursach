"""Tests for SSE stream rehydration and HITL state helpers."""

from __future__ import annotations

from backend.domain.workflow.clarification import parse_interrupt_value
from backend.domain.workflow.rerun import normalize_revision_target, normalize_rerun_target
from backend.domain.workflow.state_patch import build_state_patch


def test_state_patch_hitl_flags_plan():
    patch = build_state_patch(
        {
            "awaiting_plan_approval": True,
            "awaiting_clarification": False,
            "structure_outline": "1. Intro\n2. Body",
        }
    )
    assert patch["awaiting_plan_approval"] is True
    assert not patch.get("awaiting_clarification")


def test_state_patch_hitl_flags_clarification():
    patch = build_state_patch(
        {
            "awaiting_plan_approval": False,
            "awaiting_clarification": True,
            "pending_clarification": {"agent": "analyzer", "question": "Q?"},
        }
    )
    assert patch["awaiting_clarification"] is True
    assert patch["pending_clarification"]["agent"] == "analyzer"


def test_normalize_rerun_for_retry_after_failure():
    assert normalize_rerun_target("writer") == "writer"
    assert normalize_revision_target("coder") == "coder_gen"


def test_parse_interrupt_clarification_payload():
    payload = parse_interrupt_value(
        {"type": "clarification", "agent": "researcher", "question": "Pick one"}
    )
    assert payload["type"] == "clarification"
    assert payload["agent"] == "researcher"
