"""Port: extract plain text from uploaded file bytes."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FileTextExtractor(Protocol):
    def extract(self, data: bytes, filename: str) -> tuple[str, str]: ...
