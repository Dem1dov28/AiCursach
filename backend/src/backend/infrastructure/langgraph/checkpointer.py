"""LangGraph checkpointer — PostgreSQL with Memory fallback."""

from __future__ import annotations

import logging
from typing import Any

from backend.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

_checkpointer: Any | None = None
_backend: str = "none"


def init_checkpointer() -> None:
    """Initialize once at app startup (before workflow compile)."""
    global _checkpointer, _backend
    if _checkpointer is not None:
        return

    url = (DATABASE_URL or "").strip()
    if url:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg import Connection

            conn = Connection.connect(url, autocommit=True)
            saver = PostgresSaver(conn)
            saver.setup()
            _checkpointer = saver
            _backend = "postgresql"
            logger.info("LangGraph checkpointer: PostgreSQL")
            return
        except Exception as exc:
            logger.warning("PostgreSQL checkpointer unavailable, fallback to memory: %s", exc)

    from langgraph.checkpoint.memory import MemorySaver

    _checkpointer = MemorySaver()
    _backend = "memory"
    logger.info("LangGraph checkpointer: MemorySaver (fallback)")


def get_checkpointer() -> Any:
    if _checkpointer is None:
        init_checkpointer()
    return _checkpointer


def checkpointer_backend() -> str:
    if _checkpointer is None:
        init_checkpointer()
    return _backend
