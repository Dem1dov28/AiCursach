"""Job-scoped context for LangGraph nodes and LLM gateway."""

from __future__ import annotations

from contextvars import ContextVar, Token

_current_job_id: ContextVar[str | None] = ContextVar("aicursach_job_id", default=None)


def set_job_id(job_id: str) -> Token:
    return _current_job_id.set(job_id)


def reset_job_id(token: Token) -> None:
    _current_job_id.reset(token)


def get_job_id() -> str | None:
    return _current_job_id.get()
