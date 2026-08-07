"""Базовый контракт языкового инструмента (генерация, валидация, запуск)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ScreenshotMode = Literal["browser", "console", "none"]


@dataclass(frozen=True)
class CodeToolkit:
    """Инструмент для одного языка/стека — подключается к CoderGen и CodeRunner."""

    language: str
    display_name: str
    screenshot_mode: ScreenshotMode

    def prompt_rules(self) -> str:
        raise NotImplementedError

    def json_example(self) -> str:
        raise NotImplementedError

    def validate_files(self, files: dict[str, str]) -> dict[str, str]:
        return dict(files)

    def sanitize_files(self, files: dict[str, str]) -> dict[str, str]:
        return dict(files)

    def needs_generation_retry(self, files: dict[str, str]) -> bool:
        return False

    def retry_note(self) -> str:
        return ""

    def default_listing_file(self) -> str:
        return "main.py"

    def run(
        self,
        project_name: str,
        files: dict[str, str],
        *,
        entry_file: str = "",
    ) -> tuple[bool, str]:
        raise NotImplementedError
