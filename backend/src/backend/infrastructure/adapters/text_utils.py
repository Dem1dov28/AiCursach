"""Приведение значений из JSON LLM к строкам для join/format."""

from __future__ import annotations

from typing import Any

from backend.domain.shared.text import as_text

__all__ = ["as_text", "join_texts"]


def join_texts(values: list[Any], *, sep: str = "\n") -> str:
    return sep.join(as_text(value, sep=sep) for value in values if value not in (None, ""))
