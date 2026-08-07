"""Use case: job shared context (uploaded inputs)."""

from __future__ import annotations

from typing import Any

from backend.application.container import checkpointer_info, job_repository


class GetJobContext:
    def execute(self, job_id: str) -> dict[str, Any]:
        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            return {}
        inputs = store.get_job_inputs(job_id)
        return {
            "job_id": job_id,
            "work_type": record.work_type,
            "project_name": record.project_name,
            "inputs": [item.to_dict() for item in inputs],
            "checkpointer": checkpointer_info().backend_name(),
        }
