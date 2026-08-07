"""Track the active LangGraph node for metrics attribution."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token

_current_agent: ContextVar[str | None] = ContextVar("current_agent", default=None)


def get_current_agent() -> str | None:
    return _current_agent.get()


@contextmanager
def agent_scope(agent: str):
    token: Token = _current_agent.set(agent)
    try:
        yield
    finally:
        _current_agent.reset(token)
