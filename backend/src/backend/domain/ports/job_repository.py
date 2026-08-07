"""Port: job persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from backend.domain.jobs.records import JobInputRecord, JobRecord, JobStatus


@runtime_checkable
class JobRepository(Protocol):
    def init_schema(self) -> None: ...

    def ping(self) -> bool: ...

    def create_job(
        self,
        job_id: str,
        *,
        project_name: str,
        work_type: str,
    ) -> JobRecord: ...

    def get_job(self, job_id: str) -> JobRecord | None: ...

    def list_jobs(self, *, limit: int = 50, offset: int = 0) -> list[JobRecord]: ...

    def update_job(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        project_name: str | None = None,
        final_state: dict | None = None,
        error: str | None = None,
    ) -> None: ...

    def add_step(
        self,
        job_id: str,
        *,
        step: int,
        agent: str,
        message: str,
        detail: str = "",
    ) -> None: ...

    def save_job_input(
        self,
        job_id: str,
        *,
        kind: str,
        filename: str,
        extracted_text: str,
        content: bytes | None = None,
    ) -> None: ...

    def get_job_inputs(self, job_id: str) -> list[JobInputRecord]: ...

    def import_project_files(self, job_id: str, project_dir: Path, prefix: str) -> int: ...

    def restore_project_files(self, job_id: str, target_dir: Path) -> int: ...

    def save_zip(self, job_id: str, data: bytes, filename: str) -> None: ...

    def get_zip(self, job_id: str) -> tuple[bytes, str] | None: ...

    def add_draft_snapshot(
        self,
        job_id: str,
        *,
        step: int,
        agent: str,
        content_draft: str,
    ) -> None: ...

    def get_draft_snapshots(self, job_id: str) -> list[dict[str, Any]]: ...

    def delete_job(self, job_id: str) -> bool: ...
