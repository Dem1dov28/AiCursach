"""Use case: list LangGraph checkpoint history for a job."""

from __future__ import annotations

from typing import Any

from backend.application.container import workflow_engine


class ListJobCheckpoints:
    def execute(self, thread_id: str) -> list[dict[str, Any]]:
        workflow = workflow_engine()
        config = {"configurable": {"thread_id": thread_id}}
        items: list[dict[str, Any]] = []

        try:
            history = workflow.get_state_history(config)
        except Exception:
            return []

        for index, snap in enumerate(history):
            values = snap.values or {}
            cfg = snap.config.get("configurable", {})
            outline = str(values.get("structure_outline") or "")
            draft = str(values.get("content_draft") or "")
            metadata = snap.metadata or {}
            created_at = metadata.get("created_at") or metadata.get("ts") or ""
            items.append(
                {
                    "index": index,
                    "checkpoint_id": cfg.get("checkpoint_id", ""),
                    "next_nodes": list(snap.next or ()),
                    "topic": values.get("topic", ""),
                    "next_step": values.get("next_step", ""),
                    "revision_number": values.get("revision_number", 0),
                    "awaiting_plan_approval": bool(values.get("awaiting_plan_approval")),
                    "structure_outline_preview": (
                        outline[:120] + "…" if len(outline) > 120 else outline
                    ),
                    "has_content_draft": bool(draft.strip()),
                    "content_draft_chars": len(draft),
                    "created_at": str(created_at) if created_at else "",
                }
            )
        return items
