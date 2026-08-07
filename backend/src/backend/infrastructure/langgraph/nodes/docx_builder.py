"""DocxBuilder — сборка итогового DOCX (лабораторная или курсовая)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.domain.workflow.clarification import detect_docx_clarification
from backend.domain.workflow.work_profile import uses_coursework_docx
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import build_coursework_report, write_coursework_content_py
from backend.domain.document.annex_plan import parse_annex_plan
from backend.infrastructure.adapters.antiplagiat import (
    clamp_originality_pct,
    insert_antiplagiat_appendix,
)
from backend.infrastructure.adapters.docx_images import (
    collect_project_pngs,
    insert_figures_as_appendices,
)
from backend.infrastructure.adapters.gost_format import apply_gost_formatting
from backend.infrastructure.adapters.html_screenshots import collect_program_screenshots
from backend.infrastructure.adapters.lab_content import enrich_lab_content
from backend.infrastructure.adapters.lab_docx import write_lab_docx_stp as write_lab_docx
from backend.infrastructure.adapters.student_info import fields_from_parts
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm


def docx_builder_node(state: WorkState) -> dict:
    pre = gate_after_llm(
        state,
        "docx_builder",
        {},
        heuristic=lambda s, _: detect_docx_clarification(s),
    )

    project_name = state.get("project_name", "WorkProject")
    coursework = uses_coursework_docx(dict(state))
    logs: list[str] = []

    try:
        content = json.loads(state.get("content_draft", "{}"))
    except json.JSONDecodeError:
        content = {"raw_text": state.get("content_draft", "")}

    output_path = ""
    if coursework:
        content["topic"] = state.get("topic", "")
        if state.get("discipline"):
            content["discipline"] = state.get("discipline")
        referat = content.get("referat") if isinstance(content.get("referat"), dict) else {}
        referat = dict(referat)
        referat["originality_pct"] = clamp_originality_pct(
            state.get("originality_pct") or referat.get("originality_pct")
        )
        content["referat"] = referat
        ok_content, msg_content, _ = write_coursework_content_py(
            project_name,
            content,
            student_group=str(state.get("student_group") or ""),
            student_name=str(state.get("student_name") or ""),
            teacher_name=str(state.get("teacher_name") or ""),
            discipline=str(state.get("discipline") or ""),
            variant=str(state.get("assignment_variant") or ""),
        )
        logs.append(msg_content)
        if state.get("work_type") == "auto" and state.get("detected_work_kind"):
            logs.append(
                f"DocxBuilder: coursework path по detected_work_kind="
                f"{state.get('detected_work_kind')} (work_type=auto)"
            )
        brief_raw = state.get("work_brief") or ""
        if brief_raw:
            from backend.domain.document.work_brief import parse_work_brief

            brief = parse_work_brief(brief_raw)
            src = brief.get("structure_source") or ""
            gost = (brief.get("from_gost") or {}).get("bibliography_standard") or ""
            logs.append(
                f"DocxBuilder: materials-first brief "
                f"(structure_source={src or '—'}, bib={gost or '—'})"
            )
        if ok_content:
            ok_build, msg_build, docx = build_coursework_report(project_name)
            logs.append(msg_build)
            if docx:
                output_path = str(docx)
    else:
        content = enrich_lab_content(content, dict(state))
        content["topic"] = state.get("topic", "")

        screenshots, shot_msg = collect_program_screenshots(
            project_name,
            console_output=state.get("code_run_output", ""),
            code_language=state.get("code_language", ""),
            code_run_success=state.get("code_run_success"),
        )
        logs.append(shot_msg)

        student_fields = fields_from_parts(
            group=state.get("student_group", ""),
            student_name=state.get("student_name", ""),
            teacher_name=state.get("teacher_name", ""),
            variant=state.get("assignment_variant", ""),
            student_info=state.get("student_info", ""),
        )
        example_docx = state.get("example_docx_path", "")
        example_path = Path(example_docx) if example_docx else None

        ok_lab, msg_lab, docx = write_lab_docx(
            project_name,
            content,
            student_fields=student_fields,
            example_docx=example_path,
            screenshot_paths=screenshots,
            console_output=state.get("code_run_output", ""),
            code_language=state.get("code_language", ""),
            code_run_success=state.get("code_run_success"),
        )
        logs.append(msg_lab)
        if docx:
            output_path = str(docx)

    if output_path and coursework:
        shot = str(state.get("antiplagiat_screenshot") or "").strip()
        if shot:
            ok_ap, msg_ap = insert_antiplagiat_appendix(
                output_path,
                shot,
                letter="А",
                originality_pct=clamp_originality_pct(state.get("originality_pct")),
            )
            logs.append(msg_ap if ok_ap else f"Антиплагиат: {msg_ap}")
        pngs = collect_project_pngs(project_name)
        plan = parse_annex_plan(state.get("annex_plan"))
        n, msg_img = insert_figures_as_appendices(
            output_path,
            pngs,
            project_name=project_name,
            annex_plan=plan if plan.get("appendices") else None,
        )
        logs.append(msg_img if n else "PNG/приложения: нечего вставлять")

    if output_path:
        ok_gost, msg_gost, formatted = apply_gost_formatting(output_path)
        logs.append(msg_gost)
        if ok_gost:
            output_path = str(formatted)

    result = {
        "tool_log": logs,
        "output_docx_path": output_path,
    }
    result.update(pre)
    return result
