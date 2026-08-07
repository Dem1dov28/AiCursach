"""Port: scoped current job id for worker threads."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class JobContextScope(Protocol):
    def set_job_id(self, job_id: str | None) -> Any: ...

    def reset_job_id(self, token: Any) -> None: ...
