"""Canonical factory for LangGraph WorkState initial values."""

from __future__ import annotations

from typing import Any

from backend.domain.workflow.constants import DEFAULT_MAX_REVISIONS
from backend.domain.workflow.custom_pipeline import (
    custom_pipeline_flags,
    normalize_custom_pipeline,
)


def build_initial_state(
    *,
    work_type: str,
    assignment_text: str,
    example_text: str = "",
    methodical_text: str = "",
    assignment_variant: str = "",
    assignment_full_text: str = "",
    general_requirements_text: str = "",
    variant_task_text: str = "",
    project_name: str = "MyWork",
    topic: str = "",
    materials_bundle_text: str = "",
    materials_roles: dict[str, str] | None = None,
    student_info: str = "",
    student_group: str = "",
    student_name: str = "",
    teacher_name: str = "",
    example_docx_path: str = "",
    autonomy_level: str = "interactive",
    confidence_threshold: float = 0.8,
    custom_pipeline: list[str] | None = None,
    max_revisions: int = DEFAULT_MAX_REVISIONS,
) -> dict[str, Any]:
    normalized_type = work_type if work_type in ("lab", "coursework", "custom", "auto") else "auto"
    pipeline = normalize_custom_pipeline(custom_pipeline or [])
    user_defined = bool(pipeline)
    flags = custom_pipeline_flags(pipeline) if pipeline else {}
    preset_code = normalized_type == "lab"
    preset_diagrams = normalized_type == "coursework"
    needs_code = flags.get("needs_code", preset_code if normalized_type != "auto" else False)
    needs_diagrams = flags.get(
        "needs_diagrams",
        preset_diagrams if normalized_type != "auto" else False,
    )
    needs_excel = flags.get("needs_excel", False)
    needs_charts = flags.get("needs_charts", False)
    needs_annexes = flags.get(
        "needs_annexes",
        preset_diagrams if normalized_type != "auto" else False,
    )
    needs_antiplagiat = flags.get(
        "needs_antiplagiat",
        preset_diagrams if normalized_type != "auto" else False,
    )
    needs_project_init = flags.get("needs_project_init", preset_code if normalized_type != "auto" else False)

    return {
        "work_type": normalized_type,
        "assignment_text": assignment_text,
        "assignment_variant": assignment_variant,
        "assignment_full_text": assignment_full_text or assignment_text,
        "general_requirements_text": general_requirements_text,
        "variant_task_text": variant_task_text,
        "methodical_text": methodical_text,
        "example_text": example_text,
        "example_docx_path": example_docx_path,
        "project_name": project_name or "MyWork",
        "topic": topic.strip(),
        "materials_bundle_text": materials_bundle_text,
        "materials_roles": dict(materials_roles or {}),
        "work_brief": "",
        "student_info": student_info,
        "student_group": student_group,
        "student_name": student_name,
        "teacher_name": teacher_name,
        "research_findings": [],
        "tool_log": [],
        "diagram_files": [],
        "content_draft": "",
        "critique_notes": "",
        "bibliography_verified": False,
        "style_polished": False,
        "revision_number": 0,
        "awaiting_plan_approval": False,
        "awaiting_clarification": False,
        "pending_clarification": {},
        "clarification_log": [],
        "autonomy_level": autonomy_level,
        "confidence_threshold": confidence_threshold,
        "agent_confidence": 1.0,
        "citation_issues": [],
        "style_issues": [],
        "enable_style_polisher": True,
        "enable_bibliography_verifier": True,
        "force_rerun": "",
        "prompt_overrides": {},
        "max_revisions": max_revisions,
        "project_initialized": False,
        "code_generated": False,
        "code_run_done": False,
        "code_auto_retries": 0,
        "coursework_assets_done": False,
        "assets_quality": "",
        "diagrams_generated": False,
        "detected_work_kind": "",
        "discipline": "",
        "needs_code": needs_code,
        "needs_diagrams": needs_diagrams,
        "needs_excel": needs_excel,
        "needs_charts": needs_charts,
        "needs_annexes": needs_annexes,
        "annex_plan_done": False,
        "annex_builder_attempts": 0,
        "annex_plan": "",
        "annex_reserved_letters": [],
        "needs_antiplagiat": needs_antiplagiat,
        "antiplagiat_done": False,
        "antiplagiat_attempts": 0,
        "antiplagiat_screenshot": "",
        "originality_pct": 92,
        "needs_project_init": needs_project_init,
        "custom_pipeline": pipeline,
        "user_defined_pipeline": user_defined,
        "team_rationale": "",
        "task_breakdown": [],
        "awaiting_team_approval": False,
        "pending_team": {},
    }
