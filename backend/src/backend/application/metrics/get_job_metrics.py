"""Use case: read session metrics for a job."""

from __future__ import annotations

from typing import Any

from backend.application.container import app_settings, job_repository, token_metrics


class GetJobMetrics:
    def execute(self, job_id: str) -> dict[str, Any]:
        record = job_repository().get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")

        metrics = token_metrics().get(job_id).to_dict()
        final_state = record.final_state or {}
        max_revisions = int(final_state.get("max_revisions") or app_settings().max_revisions)

        return {
            "job_id": job_id,
            "status": record.status,
            "revision_number": int(final_state.get("revision_number") or 0),
            "max_revisions": max_revisions,
            **metrics,
        }
