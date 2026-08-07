"""Use case: read LangGraph state at a specific checkpoint (time travel preview)."""

from __future__ import annotations

from typing import Any

from backend.application.checkpoints._snapshot import find_checkpoint_snapshot
from backend.domain.workflow.state_patch import build_state_patch
from backend.application.container import workflow_engine


class GetCheckpointState:
    def execute(self, thread_id: str, checkpoint_id: str) -> dict[str, Any]:
        if not checkpoint_id.strip():
            raise ValueError("checkpoint_id обязателен")

        workflow = workflow_engine()
        snap = find_checkpoint_snapshot(workflow, thread_id, checkpoint_id.strip())
        if not snap or not snap.values:
            raise LookupError("Checkpoint не найден")

        values = dict(snap.values)
        metadata = snap.metadata or {}
        created_at = metadata.get("created_at") or metadata.get("ts") or ""

        return {
            "checkpoint_id": checkpoint_id.strip(),
            "next_nodes": list(snap.next or ()),
            "state": build_state_patch(values),
            "created_at": str(created_at) if created_at else "",
        }
