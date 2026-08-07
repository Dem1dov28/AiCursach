"""Use case: list writer draft snapshots for a job."""

from __future__ import annotations

from typing import Any

from backend.application.container import job_repository


class ListDraftSnapshots:
    def execute(self, job_id: str) -> list[dict[str, Any]]:
        store = job_repository()
        if not store.get_job(job_id):
            raise LookupError("Задача не найдена")
        return [
            {
                "id": item["id"],
                "step": item["step"],
                "agent": item["agent"],
                "created_at": item["created_at"],
            }
            for item in store.get_draft_snapshots(job_id)
        ]
