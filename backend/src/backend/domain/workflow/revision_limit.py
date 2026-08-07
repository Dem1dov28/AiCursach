"""Effective revision limit from workflow state."""

from __future__ import annotations

from backend.domain.workflow.work_state import WorkState

DEFAULT_MAX_REVISIONS = 3


def effective_max_revisions(state: WorkState) -> int:
    raw = state.get("max_revisions")
    if raw is None or raw == "":
        return DEFAULT_MAX_REVISIONS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_REVISIONS
    return max(1, min(value, 10))
