"""Port: resolve publication title by DOI."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DoiTitleResolver(Protocol):
    def __call__(self, doi: str) -> str | None: ...
