"""Инструмент Python."""

from __future__ import annotations

from backend.infrastructure.adapters.code_tools.base import CodeToolkit
from backend.infrastructure.adapters.code_tools.runners import run_python


class PythonToolkit(CodeToolkit):
    def __init__(self) -> None:
        super().__init__(
            language="python",
            display_name="Python",
            screenshot_mode="console",
        )

    def prompt_rules(self) -> str:
        return """- Один файл main.py с точкой входа if __name__ == "__main__"
- Только стандартная библиотека Python, без pip-зависимостей
- Вывод через print()"""

    def json_example(self) -> str:
        return """{
  "entry_file": "main.py",
  "files": {
    "main.py": "# -*- coding: utf-8 -*-\\nif __name__ == '__main__':\\n    print('Hello')"
  },
  "run_hint": "python main.py"
}"""

    def default_listing_file(self) -> str:
        return "main.py"

    def run(self, project_name: str, files: dict[str, str], *, entry_file: str = "") -> tuple[bool, str]:
        return run_python(project_name, files, entry_file)


TOOLKIT = PythonToolkit()
