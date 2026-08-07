"""LangGraph run configuration for a job thread."""

from __future__ import annotations

from typing import Any


def graph_config(thread_id: str, *, recursion_limit: int) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }
