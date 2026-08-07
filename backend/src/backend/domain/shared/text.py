"""Pure text helpers for domain layer."""

from __future__ import annotations

from typing import Any


def as_text(value: Any, *, sep: str = "\n") -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [as_text(item, sep=sep) for item in value]
        return sep.join(part for part in parts if part)
    if isinstance(value, dict):
        parts = [f"{key}: {as_text(val, sep=' ')}" for key, val in value.items()]
        return sep.join(parts)
    return str(value)
