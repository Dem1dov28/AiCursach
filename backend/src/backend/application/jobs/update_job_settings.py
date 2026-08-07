"""Use case: update per-job workflow settings."""

from __future__ import annotations

import logging

from backend.application.container import app_settings, event_publisher, job_repository, workflow_engine
from backend.application.workflow.graph_config import graph_config
from backend.domain.workflow.autonomy import normalize_autonomy_level
from backend.domain.workflow.state_patch import build_state_patch

logger = logging.getLogger(__name__)


class UpdateJobSettings:
    def execute(
        self,
        job_id: str,
        *,
        max_revisions: int | None = None,
        autonomy_level: str | None = None,
        confidence_threshold: float | None = None,
        enable_style_polisher: bool | None = None,
        enable_bibliography_verifier: bool | None = None,
        publish_events: bool = True,
    ) -> dict:
        store = job_repository()
        record = store.get_job(job_id)
        if not record:
            raise LookupError("Задача не найдена")

        final_state = dict(record.final_state or {})
        graph_updates: dict = {}

        if max_revisions is not None:
            if max_revisions < 1 or max_revisions > 10:
                raise ValueError("max_revisions должен быть от 1 до 10")
            final_state["max_revisions"] = max_revisions
            graph_updates["max_revisions"] = max_revisions

        if autonomy_level is not None:
            level = normalize_autonomy_level(autonomy_level)
            final_state["autonomy_level"] = level
            graph_updates["autonomy_level"] = level

        if confidence_threshold is not None:
            if confidence_threshold < 0.5 or confidence_threshold > 0.99:
                raise ValueError("confidence_threshold должен быть от 0.5 до 0.99")
            final_state["confidence_threshold"] = confidence_threshold
            graph_updates["confidence_threshold"] = confidence_threshold

        if enable_style_polisher is not None:
            final_state["enable_style_polisher"] = enable_style_polisher
            graph_updates["enable_style_polisher"] = enable_style_polisher
            if not enable_style_polisher:
                final_state["style_polished"] = True

        if enable_bibliography_verifier is not None:
            final_state["enable_bibliography_verifier"] = enable_bibliography_verifier
            graph_updates["enable_bibliography_verifier"] = enable_bibliography_verifier
            if not enable_bibliography_verifier:
                final_state["bibliography_verified"] = True

        if not graph_updates:
            raise ValueError("Нет параметров для обновления")

        store.update_job(job_id, final_state=final_state)

        config = graph_config(job_id, recursion_limit=app_settings().graph_recursion_limit)
        try:
            workflow_engine().update_state(config, graph_updates)
        except Exception as exc:
            logger.warning("LangGraph update_state failed for job %s: %s", job_id, exc)

        result = {"job_id": job_id, **graph_updates}
        if publish_events:
            patch = build_state_patch(final_state)
            if patch:
                event_publisher().publish(job_id, {"type": "state_patch", "patch": patch})
        return result
