"""Pure builder for SSE/UI state patches."""

from __future__ import annotations

from typing import Any

_STATE_KEYS = (
    "topic",
    "structure_outline",
    "content_draft",
    "critique_notes",
    "revision_number",
    "next_step",
    "current_sub_task",
    "awaiting_plan_approval",
    "awaiting_clarification",
    "awaiting_team_approval",
    "pending_clarification",
    "pending_team",
    "custom_pipeline",
    "team_rationale",
    "task_breakdown",
    "detected_work_kind",
    "discipline",
    "work_brief",
    "materials_roles",
    "autonomy_level",
    "confidence_threshold",
    "agent_confidence",
    "citation_issues",
        "style_issues",
    "enable_style_polisher",
    "enable_bibliography_verifier",
    "max_revisions",
)

_CONTENT_DRAFT_LIMIT = 8000


def build_state_patch(merged: dict, *, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for key in _STATE_KEYS:
        value = merged.get(key)
        if value is None or value == "" or value == []:
            continue
        if key == "content_draft" and isinstance(value, str) and len(value) > _CONTENT_DRAFT_LIMIT:
            patch[key] = value[:_CONTENT_DRAFT_LIMIT]
            patch["content_draft_truncated"] = True
        else:
            patch[key] = value
    if metrics:
        patch.update(metrics)
    return patch
