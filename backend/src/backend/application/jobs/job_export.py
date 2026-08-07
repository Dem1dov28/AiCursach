"""Application helpers: workspace ZIP export and DB snapshots."""

from __future__ import annotations

from typing import Any

from backend.application.container import project_workspace


def job_workspace(job_id: str):
    return project_workspace().workspace_path(job_id)


def resolve_project_dir(project_name: str, final_state: dict[str, Any], job_id: str):
    return project_workspace().resolve_project_dir(job_id, project_name, final_state)


def build_zip_bytes(
    project_name: str, job_id: str, final_state: dict[str, Any]
) -> tuple[bytes, str]:
    return project_workspace().build_zip(job_id, project_name, final_state)


def persist_workspace_snapshot(
    job_id: str,
    project_name: str,
    final_state: dict[str, Any],
) -> None:
    project_workspace().persist_snapshot(job_id, project_name, final_state)
