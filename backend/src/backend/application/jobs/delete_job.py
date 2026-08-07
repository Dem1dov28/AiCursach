"""Use case: delete a job and related artifacts."""

from __future__ import annotations

from backend.application.container import job_repository, token_metrics
from backend.application.jobs.job_hitl import hitl


class DeleteJob:
    def execute(self, job_id: str) -> None:
        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")
        if record.status in ("running", "queued"):
            raise ValueError(
                "Нельзя удалить выполняющуюся задачу — сначала поставьте на паузу"
            )

        hitl.cleanup_job(job_id)
        token_metrics().clear(job_id)
        if not store.delete_job(job_id):
            raise LookupError("Задача не найдена")
