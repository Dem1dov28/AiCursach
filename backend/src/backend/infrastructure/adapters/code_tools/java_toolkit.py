"""Инструмент Java."""

from __future__ import annotations

import re

from backend.infrastructure.adapters.code_tools.base import CodeToolkit
from backend.infrastructure.adapters.code_tools.runners import run_java

_JAVA_EXTERNAL_IMPORT = re.compile(
    r"^\s*import\s+(?:org\.|com\.|javax\.(?!swing)|jakarta\.).+$",
    re.M,
)
_JAVA_LOGGER_LINE = re.compile(
    r"^\s*(?:private\s+)?(?:static\s+)?(?:final\s+)?Logger\s+\w+.*$",
    re.M,
)
_JAVA_LOG_CALL = re.compile(r"\b\w+\.(?:info|debug|warn|error|trace)\((.*?)\);", re.S)


class JavaToolkit(CodeToolkit):
    def __init__(self) -> None:
        super().__init__(
            language="java",
            display_name="Java",
            screenshot_mode="console",
        )

    def prompt_rules(self) -> str:
        return """- Один файл Main.java: public class Main { public static void main(String[] args) }
- ТОЛЬКО стандартная библиотека JDK: System.out.println, Scanner, java.util
- ЗАПРЕЩЕНЫ Log4j, SLF4J, Spring, Maven/Gradle, import org.* / com.*"""

    def json_example(self) -> str:
        return """{
  "entry_file": "Main.java",
  "files": {
    "Main.java": "public class Main {\\n  public static void main(String[] args) {\\n    System.out.println(\\\"Hello\\\");\\n  }\\n}"
  },
  "run_hint": "javac Main.java && java Main"
}"""

    def default_listing_file(self) -> str:
        return "Main.java"

    def sanitize_files(self, files: dict[str, str]) -> dict[str, str]:
        return {name: self._sanitize_java(content) if name.endswith(".java") else content
                for name, content in files.items()}

    def _sanitize_java(self, content: str) -> str:
        if not any(t in content for t in ("org.apache.logging", "org.slf4j", "import org.", "import com.")):
            return content
        lines: list[str] = []
        for line in content.splitlines():
            if _JAVA_EXTERNAL_IMPORT.match(line):
                continue
            if "org.apache.logging" in line or "org.slf4j" in line:
                continue
            if _JAVA_LOGGER_LINE.match(line) or "LogManager.getLogger" in line:
                continue
            lines.append(line)
        text = "\n".join(lines)
        text = _JAVA_LOG_CALL.sub(r"System.out.println(\1);", text)
        return re.sub(r"\n{3,}", "\n\n", text)

    def run(self, project_name: str, files: dict[str, str], *, entry_file: str = "") -> tuple[bool, str]:
        return run_java(project_name, entry_file)


TOOLKIT = JavaToolkit()
