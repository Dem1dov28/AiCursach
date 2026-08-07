"""Инструмент C."""

from __future__ import annotations

from backend.infrastructure.adapters.code_tools.base import CodeToolkit
from backend.infrastructure.adapters.code_tools.runners import run_c


class CToolkit(CodeToolkit):
    def __init__(self) -> None:
        super().__init__(
            language="c",
            display_name="C",
            screenshot_mode="console",
        )

    def prompt_rules(self) -> str:
        return """- Один файл main.c с функцией int main(void) или int main(int argc, char *argv[])
- Только стандартная библиотека C: stdio.h, stdlib.h, string.h, math.h
- Вывод через printf(); без внешних библиотек"""

    def json_example(self) -> str:
        return """{
  "entry_file": "main.c",
  "files": {
    "main.c": "#include <stdio.h>\\nint main(void) {\\n  printf(\\\"Hello\\\\n\\\");\\n  return 0;\\n}"
  },
  "run_hint": "gcc -std=c11 main.c -o app && ./app"
}"""

    def default_listing_file(self) -> str:
        return "main.c"

    def validate_files(self, files: dict[str, str]) -> dict[str, str]:
        valid: dict[str, str] = {}
        for name, content in files.items():
            if not isinstance(content, str):
                continue
            lower = name.lower()
            if lower.endswith(".c") or lower.endswith(".h"):
                valid[name] = content
        return valid or dict(files)

    def run(self, project_name: str, files: dict[str, str], *, entry_file: str = "") -> tuple[bool, str]:
        return run_c(project_name)


TOOLKIT = CToolkit()
