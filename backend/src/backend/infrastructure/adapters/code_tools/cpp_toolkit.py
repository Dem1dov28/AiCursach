"""Инструмент C++."""

from __future__ import annotations

from backend.infrastructure.adapters.code_tools.base import CodeToolkit
from backend.infrastructure.adapters.code_tools.runners import run_cpp


class CppToolkit(CodeToolkit):
    def __init__(self) -> None:
        super().__init__(
            language="cpp",
            display_name="C++",
            screenshot_mode="console",
        )

    def prompt_rules(self) -> str:
        return """- Один файл main.cpp с int main()
- Стандарт C++17, только заголовки STL: iostream, vector, string и т.д.
- Вывод через std::cout; без Boost и сторонних библиотек"""

    def json_example(self) -> str:
        return """{
  "entry_file": "main.cpp",
  "files": {
    "main.cpp": "#include <iostream>\\nint main() {\\n  std::cout << \\\"Hello\\\" << std::endl;\\n  return 0;\\n}"
  },
  "run_hint": "g++ -std=c++17 main.cpp -o app && ./app"
}"""

    def default_listing_file(self) -> str:
        return "main.cpp"

    def run(self, project_name: str, files: dict[str, str], *, entry_file: str = "") -> tuple[bool, str]:
        return run_cpp(project_name)


TOOLKIT = CppToolkit()
