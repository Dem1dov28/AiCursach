"""Use case: list jobs for dashboard."""

from __future__ import annotations

from typing import Any

from backend.application.container import job_repository, token_metrics
from backend.domain.workflow.state_patch import build_state_patch


class ListJobs:
    def execute(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        records = job_repository().list_jobs(limit=limit, offset=offset)
        metrics_store = token_metrics()
        items: list[dict[str, Any]] = []
        for record in records:
            payload = record.to_dict()
            patch = build_state_patch(record.final_state or {})
            metrics = metrics_store.get(record.id).to_dict()
            if patch:
                payload["state_patch"] = patch
            payload["estimated_cost_usd"] = metrics.get("estimated_cost_usd", 0)
            payload["tokens_total"] = metrics.get("tokens_total", 0)
            items.append(payload)
        return items
