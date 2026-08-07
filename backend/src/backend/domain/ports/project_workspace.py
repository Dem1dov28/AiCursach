"""Port: per-job workspace on disk (scaffold, ZIP export, snapshots)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ProjectWorkspace(Protocol):
    def workspace_path(self, job_id: str) -> Path: ...

    def ensure_workspace(self, job_id: str) -> Path: ...

    def set_projects_root(self, workspace: Path) -> Any:
        """Return opaque token for reset_projects_root."""
        ...

    def reset_projects_root(self, token: Any) -> None: ...

    def resolve_project_dir(
        self, job_id: str, project_name: str, final_state: dict[str, Any]
    ) -> Path: ...

    def persist_snapshot(
        self, job_id: str, project_name: str, final_state: dict[str, Any]
    ) -> None: ...

    def build_zip(
        self, job_id: str, project_name: str, final_state: dict[str, Any]
    ) -> tuple[bytes, str]: ...

    def cleanup_workspace(self, job_id: str) -> None: ...

    def prepare_example_docx(
        self, job_id: str, example_bytes: bytes, example_filename: str
    ) -> str: ...
