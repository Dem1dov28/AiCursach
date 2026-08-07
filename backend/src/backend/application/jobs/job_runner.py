"""Job thread runners and workflow drive loop."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

from backend.application.container import (
    app_settings,
    doi_title_resolver,
    event_publisher,
    job_context_scope,
    job_repository,
    project_workspace,
    token_metrics,
)
from backend.application.jobs.job_export import (
    build_zip_bytes,
    persist_workspace_snapshot,
    resolve_project_dir,
)
from backend.application.jobs.job_hitl import hitl
from backend.application.workflow.runner import (
    rerun_workflow,
    resume_workflow,
    stream_workflow,
)
from backend.domain.workflow.initial_state import build_initial_state
from backend.domain.quality.analyze_draft import analyze_draft_quality
from backend.domain.workflow.prompt_override import merge_prompt_override
from backend.domain.workflow.rerun import normalize_rerun_target
from backend.domain.workflow.state_patch import build_state_patch
from backend.domain.workflow.step_messages import step_message
from backend.domain.workflow.team_planner import apply_team_approval_answer

_WORKSPACE_SYNC_NODES = frozenset({
    "project_init",
    "coder_gen",
    "code_runner",
    "docx_builder",
    "assets_builder",
    "diagrammer",
    "writer",
    "bibliography_verifier",
    "style_polisher",
})


def _emit(job_id: str, event: dict[str, Any]) -> None:
    event_publisher().publish(job_id, event)


def _step_offset(job_id: str) -> int:
    record = job_repository().get_job(job_id)
    return len(record.steps) if record else 0


def on_step_factory(job_id: str, step_offset: int = 0) -> Callable[[int, str, dict, dict], None]:
    store = job_repository()

    def _context_texts() -> list[str]:
        return [
            item.extracted_text
            for item in store.get_job_inputs(job_id)
            if item.extracted_text.strip()
        ]

    def on_step(step: int, node: str, output: dict, merged: dict) -> None:
        merged = dict(merged)
        record = store.get_job(job_id)
        work_type = record.work_type if record else "lab"
        quality = analyze_draft_quality(
            str(merged.get("content_draft") or ""),
            work_type=work_type,
            context_texts=_context_texts(),
            resolve_doi_title=doi_title_resolver(),
            verify_doi=app_settings().crossref_verify,
        )
        if quality["citation_issues"]:
            merged["citation_issues"] = quality["citation_issues"]
        if quality["style_issues"]:
            merged["style_issues"] = quality["style_issues"]

        msg, detail = step_message(node, output)
        record = store.get_job(job_id)
        duplicate_breakpoint = (
            node == "breakpoint"
            and record
            and record.steps
            and record.steps[-1].get("agent") == "breakpoint"
            and record.steps[-1].get("message") == msg
        )
        if not duplicate_breakpoint:
            store.add_step(job_id, step=step_offset + step, agent=node, message=msg, detail=detail)
            _emit(
                job_id,
                {
                    "type": "step",
                    "step": step_offset + step,
                    "agent": node,
                    "message": msg,
                    "detail": detail,
                },
            )

        metrics = token_metrics().to_state_patch(job_id)
        patch = build_state_patch(merged, metrics=metrics)

        if node == "writer" and not duplicate_breakpoint:
            draft = str(merged.get("content_draft") or "")
            if draft.strip():
                store.add_draft_snapshot(
                    job_id,
                    step=step_offset + step,
                    agent=node,
                    content_draft=draft,
                )

        if duplicate_breakpoint:
            if patch:
                _emit(job_id, {"type": "state_patch", "patch": patch})
            return

        record = store.get_job(job_id)
        if record and (record.final_state or {}).get("user_pause_requested"):
            merged["user_pause_requested"] = False
            merged["user_paused"] = True
            merged["awaiting_plan_approval"] = False
            merged["awaiting_clarification"] = False
            merged["awaiting_team_approval"] = False
            merged.pop("pending_clarification", None)
            merged.pop("pending_team", None)
            hitl.prepare_pause(job_id, merged, _emit)
            hitl.signal_stream_stop(job_id)
            if patch:
                _emit(job_id, {"type": "state_patch", "patch": patch})
            return

        hitl_reason: str | None = None
        hitl_extra: dict[str, Any] = {}
        if node == "breakpoint" or merged.get("awaiting_plan_approval"):
            hitl_reason = "plan_approval"
        elif merged.get("awaiting_clarification") and merged.get("pending_clarification"):
            hitl_reason = "clarification"
            hitl_extra["clarification"] = merged.get("pending_clarification") or {}
        elif merged.get("awaiting_team_approval") and merged.get("pending_team"):
            hitl_reason = "team_approval"
            hitl_extra["team"] = merged.get("pending_team") or {}

        if hitl_reason:
            hitl.prepare_pause(job_id, merged, _emit)

        if patch:
            _emit(job_id, {"type": "state_patch", "patch": patch})

        if hitl_reason:
            _emit(
                job_id,
                {
                    "type": "breakpoint",
                    "reason": hitl_reason,
                    "patch": patch,
                    **hitl_extra,
                },
            )

        if record and (
            node in _WORKSPACE_SYNC_NODES or (step_offset + step) % 3 == 0
        ):
            try:
                persist_workspace_snapshot(job_id, record.project_name, merged)
            except Exception:
                pass

    return on_step


def finalize_success(job_id: str, project_name: str, final_state: dict[str, Any]) -> None:
    store = job_repository()
    actual_name = final_state.get("project_name") or project_name
    zip_bytes, zip_name = build_zip_bytes(project_name, job_id, final_state)
    store.save_zip(job_id, zip_bytes, zip_name)

    proj = resolve_project_dir(project_name, final_state, job_id)
    if proj.is_dir():
        store.import_project_files(job_id, proj, proj.name)

    store.update_job(job_id, status="completed", project_name=actual_name, final_state=final_state)
    record = store.get_job(job_id)
    if record:
        _emit(job_id, {"type": "done", "status": "completed", "job": record.to_dict()})


def finalize_failure(
    job_id: str,
    final_state: dict[str, Any],
    err: str,
    *,
    project_name: str = "",
) -> None:
    if project_name:
        persist_workspace_snapshot(job_id, project_name, final_state)
    store = job_repository()
    store.update_job(job_id, status="failed", final_state=final_state, error=err)
    record = store.get_job(job_id)
    if record:
        _emit(
            job_id,
            {"type": "done", "status": "failed", "job": record.to_dict(), "error": err},
        )


def continue_after_pause(
    job_id: str,
    project_name: str,
    final_state: dict[str, Any],
    payload: dict[str, Any],
    recursion_limit: int,
) -> tuple[dict[str, Any], str]:
    store = job_repository()
    store.update_job(job_id, status="running")
    _emit(job_id, {"type": "status", "status": "running"})

    step_offset = _step_offset(job_id)
    on_step = on_step_factory(job_id, step_offset=step_offset)
    updates: dict[str, Any] = {}
    if payload.get("structure_outline"):
        updates["structure_outline"] = payload["structure_outline"]

    override_agent = payload.get("rerun_from") or "writer"
    if payload.get("prompt_override"):
        updates = merge_prompt_override(
            updates,
            current_overrides=final_state.get("prompt_overrides"),
            agent=override_agent,
            override_text=payload["prompt_override"],
        )

    if payload.get("clarification_answer") is not None:
        return resume_workflow(
            thread_id=job_id,
            state_updates=updates or None,
            resume_value=payload["clarification_answer"],
            recursion_limit=recursion_limit,
            on_step=on_step,
        )

    if payload.get("team_approval_answer") is not None:
        answer = payload["team_approval_answer"]
        pipeline = answer.get("custom_pipeline") or final_state.get("custom_pipeline") or []
        updates.update(apply_team_approval_answer(default_pipeline=list(pipeline), answer=answer))
        updates["pending_team"] = {}
        return resume_workflow(
            thread_id=job_id,
            state_updates=updates or None,
            resume_value=answer,
            recursion_limit=recursion_limit,
            on_step=on_step,
        )

    if payload.get("rerun_from"):
        return rerun_workflow(
            thread_id=job_id,
            from_node=payload["rerun_from"],
            state_updates=updates or None,
            recursion_limit=recursion_limit,
            on_step=on_step,
        )

    return resume_workflow(
        thread_id=job_id,
        state_updates=updates or None,
        recursion_limit=recursion_limit,
        on_step=on_step,
    )


def drive_until_done(
    job_id: str,
    project_name: str,
    *,
    initial_state: dict[str, Any] | None,
    recursion_limit: int,
) -> None:
    store = job_repository()
    final_state: dict[str, Any] = dict(initial_state or {})
    step_offset = _step_offset(job_id)
    on_step = on_step_factory(job_id, step_offset=step_offset)

    if initial_state is not None:
        final_state, status = stream_workflow(
            initial_state,
            thread_id=job_id,
            recursion_limit=recursion_limit,
            on_step=on_step,
        )
    else:
        status = "completed"
        record = store.get_job(job_id)
        if record:
            final_state = dict(record.final_state)

    while status == "paused":
        persist_workspace_snapshot(job_id, project_name, final_state)
        store.update_job(job_id, status="paused", final_state=final_state)
        _emit(job_id, {"type": "status", "status": "paused"})
        payload = hitl.wait_for_resume(job_id)
        final_state, status = continue_after_pause(
            job_id, project_name, final_state, payload, recursion_limit
        )

    if status == "completed":
        finalize_success(job_id, project_name, final_state)


def _prepare_workspace(job_id: str, example_bytes: bytes, example_filename: str) -> tuple[Path, str]:
    ws = project_workspace()
    workspace = ws.ensure_workspace(job_id)
    example_docx_path = ws.prepare_example_docx(job_id, example_bytes, example_filename)
    return workspace, example_docx_path


def _cleanup_thread_context(
    job_id: str,
    *,
    job_ctx: Any,
    projects_token: Any,
) -> None:
    hitl.cleanup_job(job_id)
    event_publisher().close(job_id)
    token_metrics().clear(job_id)
    job_context_scope().reset_job_id(job_ctx)
    ws = project_workspace()
    ws.reset_projects_root(projects_token)
    ws.cleanup_workspace(job_id)


def run_job_thread(
    *,
    job_id: str,
    work_type: str,
    project_name: str,
    assignment_text: str,
    example_text: str,
    methodical_text: str,
    assignment_variant: str,
    assignment_full_text: str,
    general_requirements_text: str,
    variant_task_text: str,
    student_info: str,
    student_group: str,
    student_name: str,
    teacher_name: str,
    topic: str,
    example_bytes: bytes,
    example_filename: str,
    materials_bundle_text: str = "",
    materials_roles: dict[str, str] | None = None,
    recursion_limit: int,
    custom_pipeline: list[str] | None = None,
) -> None:
    store = job_repository()
    hitl.set_thread_mode(job_id, "run")
    store.update_job(job_id, status="running")
    _emit(job_id, {"type": "status", "status": "running"})

    workspace, example_docx_path = _prepare_workspace(job_id, example_bytes, example_filename)
    projects_token = project_workspace().set_projects_root(workspace)
    job_ctx = job_context_scope().set_job_id(job_id)
    final_state: dict[str, Any] = {}

    try:
        state = build_initial_state(
            work_type=work_type,
            assignment_text=assignment_text,
            assignment_full_text=assignment_full_text,
            general_requirements_text=general_requirements_text,
            variant_task_text=variant_task_text,
            example_text=example_text,
            methodical_text=methodical_text,
            assignment_variant=assignment_variant,
            project_name=project_name,
            student_info=student_info,
            student_group=student_group,
            student_name=student_name,
            teacher_name=teacher_name,
            topic=topic,
            example_docx_path=example_docx_path,
            materials_bundle_text=materials_bundle_text,
            materials_roles=materials_roles or {},
            custom_pipeline=custom_pipeline,
            max_revisions=app_settings().max_revisions,
        )
        drive_until_done(job_id, project_name, initial_state=state, recursion_limit=recursion_limit)
    except Exception as exc:
        err = str(exc)
        if "Recursion limit" in err:
            err += (
                " Увеличьте GRAPH_RECURSION_LIMIT в .env "
                f"(сейчас по умолчанию {app_settings().graph_recursion_limit})."
            )
        record = store.get_job(job_id)
        if record and record.final_state:
            final_state = dict(record.final_state)
        finalize_failure(job_id, final_state, err, project_name=project_name)
    finally:
        _cleanup_thread_context(job_id, job_ctx=job_ctx, projects_token=projects_token)


def run_continue_thread(
    *,
    job_id: str,
    structure_outline: str = "",
    clarification_answer: dict[str, Any] | None = None,
    team_approval_answer: dict[str, Any] | None = None,
) -> None:
    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return

    project_name = record.project_name
    workspace = project_workspace().ensure_workspace(job_id)
    store.restore_project_files(job_id, workspace)

    projects_token = project_workspace().set_projects_root(workspace)
    job_ctx = job_context_scope().set_job_id(job_id)
    final_state: dict[str, Any] = dict(record.final_state)

    try:
        hitl.set_thread_mode(job_id, "continue")
        payload: dict[str, Any] = {"structure_outline": structure_outline.strip()}
        if clarification_answer is not None:
            payload = {"clarification_answer": clarification_answer}
        elif team_approval_answer is not None:
            payload = {"team_approval_answer": team_approval_answer}
        final_state, status = continue_after_pause(
            job_id,
            project_name,
            final_state,
            payload,
            app_settings().graph_recursion_limit,
        )

        while status == "paused":
            persist_workspace_snapshot(job_id, project_name, final_state)
            store.update_job(job_id, status="paused", final_state=final_state)
            _emit(job_id, {"type": "status", "status": "paused"})
            payload = hitl.wait_for_resume(job_id)
            final_state, status = continue_after_pause(
                job_id, project_name, final_state, payload, app_settings().graph_recursion_limit
            )

        if status == "completed":
            finalize_success(job_id, project_name, final_state)
    except Exception as exc:
        finalize_failure(job_id, final_state, str(exc), project_name=project_name)
    finally:
        _cleanup_thread_context(job_id, job_ctx=job_ctx, projects_token=projects_token)


def run_rerun_thread(
    *,
    job_id: str,
    from_node: str,
    structure_outline: str,
    prompt_override: str = "",
) -> None:
    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return

    project_name = record.project_name
    workspace = project_workspace().ensure_workspace(job_id)
    store.restore_project_files(job_id, workspace)

    projects_token = project_workspace().set_projects_root(workspace)
    job_ctx = job_context_scope().set_job_id(job_id)
    final_state: dict[str, Any] = dict(record.final_state)

    try:
        hitl.set_thread_mode(job_id, "rerun")
        store.update_job(job_id, status="running", error="")
        _emit(job_id, {"type": "status", "status": "running"})
        step_offset = _step_offset(job_id)
        on_step = on_step_factory(job_id, step_offset=step_offset)
        updates: dict[str, Any] = {}
        if structure_outline.strip():
            updates["structure_outline"] = structure_outline.strip()
        if prompt_override.strip():
            updates = merge_prompt_override(
                updates,
                current_overrides=final_state.get("prompt_overrides"),
                agent=from_node,
                override_text=prompt_override,
            )

        final_state, status = rerun_workflow(
            thread_id=job_id,
            from_node=from_node,
            state_updates=updates or None,
            on_step=on_step,
        )

        while status == "paused":
            persist_workspace_snapshot(job_id, project_name, final_state)
            store.update_job(job_id, status="paused", final_state=final_state)
            _emit(job_id, {"type": "status", "status": "paused"})
            payload = hitl.wait_for_resume(job_id)
            final_state, status = continue_after_pause(
                job_id, project_name, final_state, payload, app_settings().graph_recursion_limit
            )

        if status == "completed":
            finalize_success(job_id, project_name, final_state)
    except Exception as exc:
        finalize_failure(job_id, final_state, str(exc), project_name=project_name)
    finally:
        _cleanup_thread_context(job_id, job_ctx=job_ctx, projects_token=projects_token)


def spawn_continue_thread(**kwargs: Any) -> None:
    threading.Thread(target=run_continue_thread, kwargs=kwargs, daemon=True).start()


def spawn_rerun_thread(**kwargs: Any) -> None:
    threading.Thread(target=run_rerun_thread, kwargs=kwargs, daemon=True).start()


def submit_retry(job_id: str) -> bool:
    """Restart a failed job from the last agent, or continue a paused one."""
    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return False
    if record.status not in ("failed", "paused"):
        return False
    if hitl.is_thread_active(job_id):
        return False

    if record.status == "paused":
        spawn_continue_thread(job_id=job_id, structure_outline="")
        return True

    last_agent = record.steps[-1]["agent"] if record.steps else "analyzer"
    node = normalize_rerun_target(last_agent)
    final_state = record.final_state or {}
    hitl.set_thread_mode(job_id, "rerun")
    spawn_rerun_thread(
        job_id=job_id,
        from_node=node,
        structure_outline=str(final_state.get("structure_outline") or ""),
    )
    return True


def start_job(**kwargs: Any) -> None:
    threading.Thread(target=run_job_thread, kwargs=kwargs, daemon=True).start()


def save_job_inputs(
    job_id: str,
    *,
    assignment_text: str,
    assignment_filename: str,
    assignment_bytes: bytes,
    example_text: str,
    example_filename: str,
    example_bytes: bytes,
    methodical_text: str,
    methodical_filename: str,
    methodical_bytes: bytes,
) -> None:
    store = job_repository()
    if assignment_text.strip() or assignment_bytes:
        store.save_job_input(
            job_id,
            kind="assignment",
            filename=assignment_filename or "assignment.txt",
            extracted_text=assignment_text,
            content=assignment_bytes or None,
        )
    store.save_job_input(
        job_id,
        kind="example",
        filename=example_filename or "example",
        extracted_text=example_text,
        content=example_bytes or None,
    )
    if methodical_text.strip() or methodical_bytes:
        store.save_job_input(
            job_id,
            kind="methodical",
            filename=methodical_filename or "methodical",
            extracted_text=methodical_text,
            content=methodical_bytes or None,
        )
