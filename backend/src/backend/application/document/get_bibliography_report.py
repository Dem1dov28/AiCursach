"""Use case: bibliography audit report for a job."""

from __future__ import annotations

from backend.application.container import app_settings, doi_title_resolver, job_repository
from backend.domain.citations.bibliography_report import (
    build_bibliography_report,
    context_texts_from_state,
)


class GetBibliographyReport:
    def execute(self, job_id: str) -> dict:
        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")

        final_state = dict(record.final_state or {})
        draft = str(final_state.get("content_draft") or "")
        if not draft.strip():
            return {
                "job_id": job_id,
                "ready": False,
                "message": "Черновик ещё не сформирован",
                "report": build_bibliography_report("", work_type=record.work_type),
            }

        settings = app_settings()
        report = build_bibliography_report(
            draft,
            work_type=record.work_type,
            context_texts=context_texts_from_state(final_state),
            resolve_doi_title=doi_title_resolver(),
            verify_doi=settings.crossref_verify,
        )
        return {
            "job_id": job_id,
            "ready": True,
            "bibliography_verified": bool(final_state.get("bibliography_verified")),
            "report": report,
        }
