"""Use case: diff between writer draft snapshots."""

from __future__ import annotations

from backend.domain.document.diff_drafts import diff_plain_text
from backend.domain.document.draft_text import draft_to_plain_text
from backend.application.container import job_repository


class GetDraftDiff:
    def execute(self, job_id: str, *, from_id: int, to_id: int) -> dict:
        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")

        snapshots = store.get_draft_snapshots(job_id)
        by_id = {item["id"]: item for item in snapshots}

        if from_id not in by_id or to_id not in by_id:
            raise LookupError("Snapshot не найден")

        before = by_id[from_id]
        after = by_id[to_id]
        work_type = record.work_type

        before_text = draft_to_plain_text(before["content_draft"], work_type=work_type)
        after_text = draft_to_plain_text(after["content_draft"], work_type=work_type)
        lines = diff_plain_text(before_text, after_text)

        return {
            "from": {"id": from_id, "step": before["step"], "agent": before["agent"]},
            "to": {"id": to_id, "step": after["step"], "agent": after["agent"]},
            "lines": [line.to_dict() for line in lines],
        }
