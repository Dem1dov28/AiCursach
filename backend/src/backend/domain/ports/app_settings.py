"""Port: read-only application settings (from env at startup)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class AppSettings(Protocol):
    @property
    def graph_recursion_limit(self) -> int: ...

    @property
    def max_revisions(self) -> int: ...

    @property
    def data_dir(self) -> Path: ...

    @property
    def crossref_verify(self) -> bool: ...
