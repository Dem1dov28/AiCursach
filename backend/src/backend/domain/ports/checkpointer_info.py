"""Port: LangGraph checkpointer backend metadata."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CheckpointerInfo(Protocol):
    def backend_name(self) -> str: ...
