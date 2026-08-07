"""Port: real-time job events (SSE)."""

from __future__ import annotations

from typing import Any, Protocol


class EventPublisher(Protocol):
    def publish(self, job_id: str, event: dict[str, Any]) -> None: ...

    def subscribe(self, job_id: str, *, maxsize: int = 256) -> Any: ...

    def unsubscribe(self, job_id: str, queue: Any) -> None: ...

    def close(self, job_id: str) -> None: ...
