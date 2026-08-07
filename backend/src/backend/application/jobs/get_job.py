"""Use cases: read job state and artifacts."""

from __future__ import annotations

from typing import Any

from backend.application.container import job_repository
from backend.domain.workflow.state_patch import build_state_patch


class GetJob:
    def execute(self, job_id: str) -> dict[str, Any] | None:
        record = job_repository().get_job(job_id)
        if not record:
            return None
        payload = record.to_dict()
        patch = build_state_patch(record.final_state or {})
        if patch:
            payload["state_patch"] = patch
        return payload


class GetJobZip:
    def execute(self, job_id: str) -> tuple[bytes, str] | None:
        return job_repository().get_zip(job_id)
