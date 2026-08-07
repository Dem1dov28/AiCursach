"""All /api/jobs/* routes."""

from __future__ import annotations

import json
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from backend.api.deps import require_llm_configured
from backend.api.http_utils import attachment_headers
from backend.application.checkpoints.get_checkpoint_state import GetCheckpointState
from backend.application.checkpoints.list_checkpoints import ListJobCheckpoints
from backend.application.checkpoints.restore_checkpoint import RestoreJobCheckpoint
from backend.application.document.get_bibliography_report import GetBibliographyReport
from backend.application.document.get_draft_diff import GetDraftDiff
from backend.application.document.list_draft_snapshots import ListDraftSnapshots
from backend.application.export.export_latex import ExportLatex
from backend.application.jobs.delete_job import DeleteJob
from backend.application.jobs.get_job import GetJob, GetJobZip
from backend.application.jobs.get_job_context import GetJobContext
from backend.application.jobs.job_executor import (
    submit_clarification,
    submit_pause,
    submit_resume,
    submit_rerun,
    submit_retry,
    submit_team_approval,
)
from backend.application.jobs.list_jobs import ListJobs
from backend.application.jobs.start_job_from_form import JobFormFiles, JobFormMeta, StartJobFromForm
from backend.application.jobs.stream_job import StreamJobEvents
from backend.application.jobs.update_job_plan import UpdateJobPlan
from backend.application.jobs.update_job_settings import UpdateJobSettings
from backend.application.metrics.get_job_metrics import GetJobMetrics

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_get_job = GetJob()
_get_zip = GetJobZip()
_list_jobs = ListJobs()
_get_context = GetJobContext()
_list_checkpoints = ListJobCheckpoints()
_get_checkpoint_state = GetCheckpointState()
_restore_checkpoint = RestoreJobCheckpoint()
_update_plan = UpdateJobPlan()
_export_latex = ExportLatex()
_get_draft_diff = GetDraftDiff()
_get_bibliography_report = GetBibliographyReport()
_get_metrics = GetJobMetrics()
_update_settings = UpdateJobSettings()
_list_snapshots = ListDraftSnapshots()
_start_job = StartJobFromForm()
_stream_job = StreamJobEvents()
_delete_job = DeleteJob()


class ResumeJobBody(BaseModel):
    structure_outline: str = ""


class UpdateJobPlanBody(BaseModel):
    structure_outline: str = Field(..., min_length=1)
    topic: str = ""


class RerunJobBody(BaseModel):
    from_node: str = Field(..., min_length=1)
    structure_outline: str = ""
    prompt_override: str = ""


class JobSettingsBody(BaseModel):
    max_revisions: int | None = Field(default=None, ge=1, le=10)
    autonomy_level: str | None = None
    confidence_threshold: float | None = Field(default=None, ge=0.5, le=0.99)
    enable_style_polisher: bool | None = None
    enable_bibliography_verifier: bool | None = None


class ClarificationAnswerBody(BaseModel):
    selected_option: str = ""
    custom_text: str = ""


class TeamApprovalBody(BaseModel):
    custom_pipeline: list[str] | None = None


def _require_job(job_id: str) -> dict:
    job = _get_job.execute(job_id)
    if not job:
        raise HTTPException(404, "Задача не найдена")
    return job


@router.post("")
async def create_job(
    example: UploadFile | None = File(default=None, description="Пример работы (необязательно)"),
    assignment: UploadFile | None = File(default=None, description="Задание (файл)"),
    methodical: UploadFile | None = File(default=None, description="Методичка"),
    materials: list[UploadFile] = File(default=[], description="Все материалы одним пакетом"),
    work_type: str = Form("auto"),
    project_name: str = Form("MyWork"),
    student_info: str = Form(""),
    student_group: str = Form(""),
    student_name: str = Form(""),
    teacher_name: str = Form(""),
    assignment_text: str = Form(""),
    assignment_variant: str = Form(""),
    topic: str = Form(""),
):
    require_llm_configured()

    assignment_data = b""
    assignment_name = ""
    if assignment is not None:
        assignment_data = await assignment.read()
        assignment_name = assignment.filename or "assignment"

    example_data = b""
    example_name = ""
    if example is not None:
        example_data = await example.read()
        example_name = example.filename or "example"

    methodical_data = b""
    methodical_name = ""
    if methodical is not None:
        methodical_data = await methodical.read()
        methodical_name = methodical.filename or "methodical"

    material_pairs: list[tuple[str, bytes]] = []
    for upload in materials:
        data = await upload.read()
        if data:
            material_pairs.append((upload.filename or "material", data))

    try:
        job_id, status = _start_job.execute(
            JobFormFiles(
                assignment_data=assignment_data,
                assignment_name=assignment_name,
                assignment_text=assignment_text,
                example_data=example_data,
                example_name=example_name,
                methodical_data=methodical_data,
                methodical_name=methodical_name,
                materials=tuple(material_pairs),
            ),
            JobFormMeta(
                work_type=work_type,
                project_name=project_name,
                student_info=student_info,
                student_group=student_group,
                student_name=student_name,
                teacher_name=teacher_name,
                assignment_variant=assignment_variant,
                topic=topic.strip(),
            ),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return {"job_id": job_id, "status": status}


@router.get("")
async def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return {"jobs": _list_jobs.execute(limit=limit, offset=offset)}


@router.get("/{job_id}")
async def job_status(job_id: str):
    return _require_job(job_id)


@router.get("/{job_id}/stream")
async def stream_job(job_id: str):
    _require_job(job_id)

    async def event_generator():
        async for chunk in _stream_job.events(job_id):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{job_id}/download")
async def download_result(job_id: str):
    job = _require_job(job_id)
    if job["status"] != "completed":
        raise HTTPException(400, f"Работа ещё не готова (статус: {job['status']})")
    packed = _get_zip.execute(job_id)
    if not packed:
        raise HTTPException(404, "Архив не найден в базе данных")
    data, filename = packed
    return Response(
        content=data,
        media_type="application/zip",
        headers=attachment_headers(filename),
    )


@router.get("/{job_id}/metrics")
async def job_metrics(job_id: str):
    _require_job(job_id)
    try:
        return _get_metrics.execute(job_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.patch("/{job_id}/settings")
async def update_job_settings(job_id: str, body: JobSettingsBody):
    job = _require_job(job_id)
    if job["status"] in ("completed", "failed"):
        raise HTTPException(400, "Нельзя менять настройки завершённой задачи")
    if (
        body.max_revisions is None
        and body.autonomy_level is None
        and body.confidence_threshold is None
        and body.enable_style_polisher is None
        and body.enable_bibliography_verifier is None
    ):
        raise HTTPException(400, "Укажите хотя бы один параметр")
    try:
        return _update_settings.execute(
            job_id,
            max_revisions=body.max_revisions,
            autonomy_level=body.autonomy_level,
            confidence_threshold=body.confidence_threshold,
            enable_style_polisher=body.enable_style_polisher,
            enable_bibliography_verifier=body.enable_bibliography_verifier,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/{job_id}/clarification")
async def answer_clarification(job_id: str, body: ClarificationAnswerBody):
    _require_job(job_id)
    if not body.selected_option.strip() and not body.custom_text.strip():
        raise HTTPException(400, "Укажите вариант или свой ответ")
    if not submit_clarification(
        job_id,
        selected_option=body.selected_option,
        custom_text=body.custom_text,
    ):
        raise HTTPException(409, "Уточнение ещё не готово — повторите через секунду")
    return {"ok": True, "job_id": job_id}


@router.get("/{job_id}/context")
async def job_context(job_id: str):
    _require_job(job_id)
    return _get_context.execute(job_id)


@router.get("/{job_id}/checkpoints")
async def job_checkpoints(job_id: str):
    _require_job(job_id)
    return {"job_id": job_id, "checkpoints": _list_checkpoints.execute(job_id)}


@router.get("/{job_id}/checkpoints/{checkpoint_id}")
async def job_checkpoint_state(job_id: str, checkpoint_id: str):
    _require_job(job_id)
    try:
        return _get_checkpoint_state.execute(job_id, checkpoint_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/{job_id}/checkpoints/{checkpoint_id}/restore")
async def restore_job_checkpoint(job_id: str, checkpoint_id: str):
    job = _require_job(job_id)
    if job["status"] in ("running", "queued"):
        raise HTTPException(400, "Нельзя восстановить checkpoint во время выполнения")
    try:
        return _restore_checkpoint.execute(job_id, checkpoint_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.patch("/{job_id}/plan")
async def update_job_plan(job_id: str, body: UpdateJobPlanBody):
    job = _require_job(job_id)
    if job["status"] != "paused":
        raise HTTPException(400, f"План можно сохранять только на паузе (статус: {job['status']})")
    try:
        return _update_plan.execute(
            job_id,
            structure_outline=body.structure_outline,
            topic=body.topic or None,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{job_id}/bibliography-report")
async def job_bibliography_report(job_id: str):
    _require_job(job_id)
    try:
        return _get_bibliography_report.execute(job_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{job_id}/draft-snapshots")
async def job_draft_snapshots(job_id: str):
    _require_job(job_id)
    try:
        snapshots = _list_snapshots.execute(job_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"job_id": job_id, "snapshots": snapshots}


@router.get("/{job_id}/draft-diff")
async def job_draft_diff(
    job_id: str,
    from_id: int = Query(..., alias="from"),
    to_id: int = Query(..., alias="to"),
):
    _require_job(job_id)
    try:
        return _get_draft_diff.execute(job_id, from_id=from_id, to_id=to_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{job_id}/export/latex")
async def export_job_latex(job_id: str):
    _require_job(job_id)
    try:
        latex, filename = _export_latex.execute(job_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    encoded = quote(filename)
    return Response(
        content=latex.encode("utf-8"),
        media_type="application/x-tex",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.post("/{job_id}/resume")
async def resume_paused_job(job_id: str, body: ResumeJobBody):
    job = _require_job(job_id)
    if job["status"] != "paused":
        raise HTTPException(400, f"Задача не на паузе (статус: {job['status']})")
    if not submit_resume(job_id, structure_outline=body.structure_outline):
        raise HTTPException(409, "Не удалось возобновить задачу")
    return {"ok": True, "job_id": job_id}


@router.post("/{job_id}/team")
async def approve_team(job_id: str, body: TeamApprovalBody):
    job = _require_job(job_id)
    patch = job.get("state_patch") or {}
    awaiting = bool(patch.get("awaiting_team_approval"))
    if job["status"] not in ("paused", "running") or (job["status"] == "running" and not awaiting):
        raise HTTPException(400, f"Нет ожидания утверждения команды (статус: {job['status']})")
    if not submit_team_approval(job_id, custom_pipeline=body.custom_pipeline):
        raise HTTPException(409, "Не удалось утвердить команду агентов")
    return {"ok": True, "job_id": job_id}


@router.post("/{job_id}/rerun")
async def rerun_from_node(job_id: str, body: RerunJobBody):
    job = _require_job(job_id)
    if job["status"] in ("running", "queued"):
        raise HTTPException(400, "Нельзя перезапустить узел во время выполнения")
    if not submit_rerun(
        job_id,
        from_node=body.from_node,
        structure_outline=body.structure_outline,
        prompt_override=body.prompt_override,
    ):
        raise HTTPException(409, "Не удалось перезапустить с выбранного узла")
    return {"ok": True, "job_id": job_id, "from_node": body.from_node}


@router.post("/{job_id}/retry")
async def retry_job(job_id: str):
    job = _require_job(job_id)
    if job["status"] not in ("failed", "paused"):
        raise HTTPException(400, f"Повтор доступен только для failed/paused (статус: {job['status']})")
    if not submit_retry(job_id):
        raise HTTPException(409, "Не удалось перезапустить задачу")
    return {"ok": True, "job_id": job_id}


@router.post("/{job_id}/pause")
async def pause_job(job_id: str):
    job = _require_job(job_id)
    if job["status"] == "paused":
        return {"ok": True, "job_id": job_id, "status": "paused"}
    if job["status"] != "running":
        raise HTTPException(400, f"Пауза доступна только для running (статус: {job['status']})")
    if not submit_pause(job_id):
        raise HTTPException(409, "Не удалось поставить задачу на паузу")
    return {"ok": True, "job_id": job_id, "status": "pausing"}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    try:
        _delete_job.execute(job_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "job_id": job_id}
