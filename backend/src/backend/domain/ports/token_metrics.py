"""Port: in-memory LLM token metrics per job."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.domain.metrics.token_usage import SessionMetrics


@runtime_checkable
class TokenMetricsStore(Protocol):
    def get(self, job_id: str) -> SessionMetrics: ...

    def clear(self, job_id: str) -> None: ...

    def to_state_patch(self, job_id: str) -> dict[str, Any]: ...

    def record_current(self, usage: Any, *, agent: str | None = None) -> SessionMetrics | None: ...
