"""Port: LangGraph workflow execution."""

from __future__ import annotations

from typing import Any, Protocol


class WorkflowEngine(Protocol):
    def stream(self, input_state: Any, *, config: dict[str, Any]) -> Any: ...

    def update_state(self, config: dict[str, Any], values: dict[str, Any] | None) -> Any: ...

    def get_state(self, config: dict[str, Any]) -> Any: ...

    def get_state_history(self, config: dict[str, Any]) -> Any: ...
