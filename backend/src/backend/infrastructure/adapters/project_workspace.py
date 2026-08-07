"""Filesystem adapter for per-job project workspaces."""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path
from typing import Any

from backend.core.paths import lab_zip_skip, reset_projects_root, set_projects_root
from backend.domain.citations.bibliography_report import (
    build_bibliography_report,
    context_texts_from_state,
    render_bibliography_report_html,
)
from backend.domain.ports.doi_resolver import DoiTitleResolver
from backend.domain.ports.job_repository import JobRepository


class FilesystemProjectWorkspace:
    def __init__(
        self,
        *,
        data_dir: Path,
        job_repository: JobRepository,
        resolve_doi_title: DoiTitleResolver,
    ) -> None:
        self._data_dir = data_dir
        self._jobs = job_repository
        self._resolve_doi_title = resolve_doi_title

    def _jobs_dir(self) -> Path:
        return self._data_dir / "jobs"

    def workspace_path(self, job_id: str) -> Path:
        return self._jobs_dir() / job_id / "workspace"

    def ensure_workspace(self, job_id: str) -> Path:
        workspace = self.workspace_path(job_id)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def set_projects_root(self, workspace: Path) -> Any:
        return set_projects_root(workspace)

    def reset_projects_root(self, token: Any) -> None:
        reset_projects_root(token)

    def resolve_project_dir(
        self, job_id: str, project_name: str, final_state: dict[str, Any]
    ) -> Path:
        workspace = self.workspace_path(job_id)
        actual_name = (final_state.get("project_name") or project_name or "").strip()

        if actual_name:
            proj = workspace / actual_name
            if proj.is_dir():
                return proj

        for key in ("project_path", "output_docx_path"):
            raw = final_state.get(key, "")
            if not raw:
                continue
            path = Path(raw)
            if path.is_dir():
                return path
            if path.is_file():
                for parent in path.parents:
                    if parent.parent == workspace:
                        return parent

        return workspace / (actual_name or project_name or "MyWork")

    def build_zip(
        self, job_id: str, project_name: str, final_state: dict[str, Any]
    ) -> tuple[bytes, str]:
        proj = self.resolve_project_dir(job_id, project_name, final_state)
        archive_name = proj.name if proj.is_dir() else (
            final_state.get("project_name") or project_name
        )
        filename = f"{archive_name}_work.zip"

        work_type = final_state.get("work_type", "lab")
        buffer = io.BytesIO()
        added = 0
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if proj.is_dir():
                for path in proj.rglob("*"):
                    if not path.is_file() or ".git" in path.parts:
                        continue
                    if work_type == "lab" and lab_zip_skip(path, proj):
                        continue
                    arc = Path(archive_name) / path.relative_to(proj)
                    zf.write(path, arc)
                    added += 1

            docx = final_state.get("output_docx_path", "")
            if docx:
                docx_path = Path(docx)
                if docx_path.is_file():
                    arc = Path(archive_name) / "Отчет" / docx_path.name
                    if arc.as_posix() not in {item.filename for item in zf.infolist()}:
                        zf.write(docx_path, arc)
                        added += 1

            draft = str(final_state.get("content_draft") or "").strip()
            if draft:
                report = build_bibliography_report(
                    draft,
                    work_type=str(final_state.get("work_type") or "auto"),
                    context_texts=context_texts_from_state(final_state),
                    verify_doi=False,
                    resolve_doi_title=self._resolve_doi_title,
                )
                html = render_bibliography_report_html(report)
                arc = Path(archive_name) / "bibliography_report.html"
                zf.writestr(arc.as_posix(), html.encode("utf-8"))
                added += 1

        if added == 0:
            raise RuntimeError(
                f"Не удалось собрать архив: папка проекта не найдена ({proj}). "
                "Проверьте журнал Builder."
            )

        return buffer.getvalue(), filename

    def persist_snapshot(
        self, job_id: str, project_name: str, final_state: dict[str, Any]
    ) -> None:
        proj = self.resolve_project_dir(job_id, project_name, final_state)
        if proj.is_dir():
            self._jobs.import_project_files(job_id, proj, proj.name)

    def cleanup_workspace(self, job_id: str) -> None:
        shutil.rmtree(self.workspace_path(job_id), ignore_errors=True)

    def prepare_example_docx(
        self, job_id: str, example_bytes: bytes, example_filename: str
    ) -> str:
        workspace = self.ensure_workspace(job_id)
        if not example_filename.lower().endswith(".docx") or not example_bytes:
            return ""
        inputs = workspace / "_inputs"
        inputs.mkdir(parents=True, exist_ok=True)
        example_file = inputs / "example.docx"
        example_file.write_bytes(example_bytes)
        return str(example_file)
