"""Helpers for LangGraph checkpoint snapshots."""

from __future__ import annotations

from typing import Any


def find_checkpoint_snapshot(workflow: Any, thread_id: str, checkpoint_id: str):
    config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}
    try:
        snap = workflow.get_state(config)
        if snap and snap.values:
            return snap
    except Exception:
        pass

    try:
        history = workflow.get_state_history({"configurable": {"thread_id": thread_id}})
    except Exception:
        return None

    for snap in history:
        cfg = snap.config.get("configurable", {})
        if cfg.get("checkpoint_id") == checkpoint_id:
            return snap
    return None
