"""Analyzer — разбор задания, методички и примера."""

from __future__ import annotations

from backend.domain.document.discipline_outline import ensure_methods_in_outline
from backend.domain.document.work_brief import (
    brief_summary_for_hitl,
    merge_volume_targets,
    parse_work_brief,
    work_brief_to_json,
)
from backend.domain.workflow.clarification import detect_analyzer_clarification
from backend.domain.workflow.team_planner import (
    apply_team_approval_answer,
    assemble_team_from_analysis,
    build_team_interrupt_payload,
)
from backend.domain.workflow.work_profile import (
    analysis_flags,
    normalize_discipline,
    normalize_work_kind,
)
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.code_language import resolve_code_language
from backend.infrastructure.adapters.text_utils import as_text
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import ANALYZER_PROMPT


def analyzer_node(state: WorkState) -> dict:
    llm = get_llm()
    work_type = state.get("work_type", "auto")
    general = (state.get("general_requirements_text") or state.get("assignment_text") or "")[:6000]
    variant_task = (state.get("variant_task_text") or "")[:4000]
    assignment_summary = (state.get("assignment_text") or "")[:4000]
    user_topic = (state.get("topic") or "").strip()
    materials_bundle = (state.get("materials_bundle_text") or "").strip()
    roles = state.get("materials_roles") or {}
    roles_text = (
        ", ".join(f"{name}→{role}" for name, role in roles.items())
        if isinstance(roles, dict) and roles
        else "(не размечены — определи роли сам)"
    )
    prompt = ANALYZER_PROMPT.format(
        work_type=work_type,
        methodical_text=(state.get("methodical_text") or "")[:8000] or "(не загружена отдельно)",
        general_requirements_text=general,
        variant_task_text=variant_task or "(вариант не выделен — смотри сводку задания)",
        assignment_text=assignment_summary,
        assignment_variant=state.get("assignment_variant") or "не указан — всё задание целиком",
        example_text=(state.get("example_text") or "не предоставлен")[:8000],
        materials_bundle_text=materials_bundle[:12000]
        if materials_bundle
        else "(материалы переданы отдельными полями выше)",
        materials_roles=roles_text,
        user_topic=user_topic or "(не указана — извлеки из задания варианта)",
    )
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {}

    project_name = data.get("project_name") or state.get("project_name") or "WorkProject"
    project_name = "".join(c for c in project_name if c.isalnum() or c in "_-")[:40] or "WorkProject"

    flags = analysis_flags(data)
    if work_type == "lab" and "needs_code" not in data:
        flags["needs_code"] = True
        flags["needs_project_init"] = True
    elif work_type == "coursework" and "needs_diagrams" not in data:
        flags["needs_diagrams"] = True

    requirements = as_text(data.get("requirements") or raw[:2000])
    structure_outline = as_text(data.get("structure_outline", ""))

    code_language = resolve_code_language(
        data.get("code_language"),
        variant_task or state.get("assignment_text", ""),
        state.get("general_requirements_text", "") or state.get("methodical_text", ""),
        requirements,
        state.get("example_text", ""),
    )
    if not flags["needs_code"]:
        code_language = "none"

    diagram_types = data.get("diagram_types", ["usecase", "idef0"])
    if isinstance(diagram_types, list):
        diagram_types_str = ", ".join(as_text(item) for item in diagram_types)
    else:
        diagram_types_str = as_text(diagram_types)

    methodical = (state.get("methodical_text") or "").strip()
    needs_research = data.get("needs_research")
    if needs_research is None:
        needs_research = len(methodical) < 400

    detected_work_kind = normalize_work_kind(data.get("detected_work_kind"))
    discipline = normalize_discipline(data.get("discipline"))
    structure_outline = ensure_methods_in_outline(structure_outline, discipline)

    # Topic: never take from example when user/assignment provided one.
    topic = user_topic or as_text(data.get("topic") or "Учебная работа")

    brief = parse_work_brief(data.get("work_brief"))
    if not brief.get("structure_source"):
        example = (state.get("example_text") or "").lower()
        if "пример не загружен" not in example and len(state.get("example_text") or "") > 400:
            brief["structure_source"] = "example"
        elif methodical:
            brief["structure_source"] = "methodical"
        else:
            brief["structure_source"] = "discipline_fallback"
    targets = merge_volume_targets(brief, methodical_text=methodical)
    brief["volume_targets"] = targets
    work_brief_json = work_brief_to_json(brief)

    result = {
        "topic": topic,
        "detected_work_kind": detected_work_kind,
        "discipline": discipline,
        "requirements": requirements,
        "structure_outline": structure_outline,
        "work_brief": work_brief_json,
        "project_name": project_name,
        "needs_code": flags["needs_code"],
        "needs_project_init": flags["needs_project_init"],
        "needs_diagrams": flags["needs_diagrams"],
        "needs_excel": flags["needs_excel"],
        "needs_charts": flags["needs_charts"],
        "needs_research": bool(needs_research),
        "code_language": code_language,
        "diagram_types": diagram_types_str,
        "current_sub_task": "Анализ задания завершён",
    }

    result.update(
        gate_after_llm(
            state,
            "analyzer",
            data,
            heuristic=lambda s, d: detect_analyzer_clarification(s, d),
        )
    )

    if state.get("user_defined_pipeline"):
        return result

    pipeline, rationale, breakdown = assemble_team_from_analysis(
        {**state, **result, **data},
        work_type=work_type,
    )
    brief_blurb = brief_summary_for_hitl(brief, structure_outline)
    if brief_blurb:
        rationale = (rationale + " | Материалы: " + brief_blurb).strip()
    result["custom_pipeline"] = pipeline
    result["team_rationale"] = rationale
    result["task_breakdown"] = breakdown

    from langgraph.types import interrupt

    payload = build_team_interrupt_payload(
        pipeline=pipeline,
        rationale=rationale,
        task_breakdown=breakdown,
        topic=str(result.get("topic") or ""),
        detected_work_kind=detected_work_kind,
        discipline=discipline,
        structure_outline=structure_outline,
        work_brief_summary=brief_blurb,
        structure_source=str(brief.get("structure_source") or ""),
    )
    answer = interrupt(payload)
    result.update(
        apply_team_approval_answer(default_pipeline=pipeline, answer=answer),
    )
    result["current_sub_task"] = "Команда агентов утверждена — запуск выполнения"

    return result
