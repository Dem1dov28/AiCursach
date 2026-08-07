"""Use case: rewind job workflow state to a LangGraph checkpoint."""

from __future__ import annotations

from typing import Any

from backend.application.container import event_publisher, job_repository, workflow_engine
from backend.application.checkpoints._snapshot import find_checkpoint_snapshot
from backend.application.jobs.get_job import GetJob
from backend.domain.workflow.state_patch import build_state_patch


class RestoreJobCheckpoint:
    def execute(self, job_id: str, checkpoint_id: str) -> dict[str, Any]:
        cid = checkpoint_id.strip()
        if not cid:
            raise ValueError("checkpoint_id обязателен")

        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")
        if record.status in ("running", "queued"):
            raise ValueError("Нельзя восстановить checkpoint во время выполнения")

        workflow = workflow_engine()
        snap = find_checkpoint_snapshot(workflow, job_id, cid)
        if not snap or not snap.values:
            raise LookupError("Checkpoint не найден")

        values = dict(snap.values)
        workflow.update_state(snap.config, values)

        store.update_job(job_id, status="paused", final_state=values, error="")
        patch = build_state_patch(values)

        event_publisher().publish(job_id, {"type": "status", "status": "paused"})
        if patch:
            event_publisher().publish(job_id, {"type": "state_patch", "patch": patch})

        job_dict = GetJob().execute(job_id)
        if job_dict:
            event_publisher().publish(job_id, {"type": "snapshot", "job": job_dict})

        return {"ok": True, "job_id": job_id, "checkpoint_id": cid, "patch": patch}
