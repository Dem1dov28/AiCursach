"""Общее состояние мультиагентного workflow."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

WorkType = Literal["lab", "coursework", "custom", "auto"]


class WorkState(TypedDict, total=False):
    """Состояние, которое передаётся между агентами LangGraph."""

    # Вход
    work_type: WorkType
    assignment_text: str
    assignment_full_text: str
    general_requirements_text: str
    variant_task_text: str
    assignment_variant: str
    example_text: str
    example_docx_path: str
    methodical_text: str
    project_name: str
    student_info: str
    student_group: str
    student_name: str
    teacher_name: str

    # Проект
    project_initialized: bool
    project_path: str

    # Анализ задания
    requirements: str
    structure_outline: str
    topic: str
    detected_work_kind: str
    discipline: str
    needs_research: bool
    needs_project_init: bool
    materials_bundle_text: str
    materials_roles: dict
    work_brief: str

    # Исследование
    research_findings: Annotated[list[str], operator.add]

    # Контент
    content_draft: str

    # Coder
    needs_code: bool
    code_language: str
    code_generated: bool
    code_run_done: bool
    code_entry_file: str
    code_files: str
    code_run_output: str
    code_run_success: bool
    code_auto_retries: int
    coder_gen_attempts: int

    # Diagrammer
    needs_diagrams: bool
    diagram_types: str
    diagrams_generated: bool
    diagrammer_attempts: int
    diagram_files: Annotated[list[str], operator.add]

    # Coursework (Excel / графики)
    needs_excel: bool
    needs_charts: bool
    coursework_assets_done: bool
    assets_builder_attempts: int
    # skipped | iouz | topic | placeholder | failed | ""
    assets_quality: str

    # Annex plan (приложения)
    needs_annexes: bool
    annex_plan_done: bool
    annex_builder_attempts: int
    annex_plan: str
    annex_reserved_letters: list[str]

    # Antiplagiat
    needs_antiplagiat: bool
    antiplagiat_done: bool
    antiplagiat_attempts: int
    antiplagiat_screenshot: str
    originality_pct: int

    # Сборка
    tool_log: Annotated[list[str], operator.add]
    output_docx_path: str

    # Контроль качества
    critique_notes: str
    critique_rerun: str
    revision_number: int
    bibliography_verified: bool
    bibliography_attempts: int
    style_polished: bool
    style_polisher_attempts: int
    enable_style_polisher: bool
    enable_bibliography_verifier: bool

    # Human-in-the-loop
    awaiting_plan_approval: bool
    awaiting_clarification: bool
    pending_clarification: dict[str, Any]
    clarification_log: Annotated[list[dict[str, str]], operator.add]
    autonomy_level: str
    confidence_threshold: float
    agent_confidence: float
    citation_issues: list[dict[str, str]]
    style_issues: list[dict[str, str | int]]
    force_rerun: str
    prompt_overrides: dict[str, str]
    max_revisions: int

    # Маршрутизация
    next_step: str
    current_sub_task: str

    # Пользовательский граф (blank canvas)
    custom_pipeline: list[str]
    user_defined_pipeline: bool
    team_rationale: str
    task_breakdown: list[dict[str, Any]]
    awaiting_team_approval: bool
    pending_team: dict[str, Any]
