"""Use case: save HITL plan draft to LangGraph state and job store (without resume)."""

from __future__ import annotations

from typing import Any

from backend.application.container import app_settings, event_publisher, job_repository, workflow_engine
from backend.application.workflow.graph_config import graph_config
from backend.domain.workflow.state_patch import build_state_patch


class UpdateJobPlan:
    def execute(
        self,
        job_id: str,
        *,
        structure_outline: str,
        topic: str | None = None,
    ) -> dict[str, Any]:
        outline = structure_outline.strip()
        if not outline:
            raise ValueError("План не может быть пустым")

        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")
        if record.status != "paused":
            raise ValueError("План можно сохранять только на паузе HITL")

        updates: dict[str, Any] = {
            "structure_outline": outline,
            "awaiting_plan_approval": True,
        }
        if topic is not None:
            topic_text = topic.strip()
            if topic_text:
                updates["topic"] = topic_text

        config = graph_config(job_id, recursion_limit=app_settings().graph_recursion_limit)
        workflow_engine().update_state(config, updates)

        final_state = dict(record.final_state or {})
        final_state.update(updates)
        store.update_job(job_id, final_state=final_state)

        patch = build_state_patch(final_state)
        if patch:
            event_publisher().publish(job_id, {"type": "state_patch", "patch": patch})

        return {"job_id": job_id, "patch": patch}
