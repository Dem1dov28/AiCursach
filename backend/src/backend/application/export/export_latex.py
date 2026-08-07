"""Use case: export content draft as LaTeX."""

from __future__ import annotations

from backend.domain.document.latex_export import build_latex_document
from backend.application.container import job_repository


class ExportLatex:
    def execute(self, job_id: str) -> tuple[str, str]:
        record = job_repository().get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")

        state = record.final_state or {}
        content = str(state.get("content_draft") or "")
        if not content.strip():
            raise ValueError("Черновик ещё не сгенерирован")

        title = str(state.get("topic") or record.project_name or "Учебная работа")
        latex = build_latex_document(
            content_draft=content,
            work_type=record.work_type,
            title=title,
            structure_outline=str(state.get("structure_outline") or ""),
        )
        filename = f"{record.project_name or job_id}.tex"
        return latex, filename
