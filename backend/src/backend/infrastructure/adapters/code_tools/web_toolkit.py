"""Инструмент HTML/CSS/JavaScript (веб-проекты)."""

from __future__ import annotations

from backend.infrastructure.llm.gateway import llm_text
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.code_tools.base import CodeToolkit
from backend.infrastructure.adapters.code_tools.runners import run_web
from backend.infrastructure.adapters.web_project import (
    CODER_WEB_RETRY_NOTE,
    javascript_project_complete,
    missing_web_parts,
    validate_javascript_files,
)
from backend.infrastructure.adapters.source_sanitize import apply_source_sanitize


class WebToolkit(CodeToolkit):
    def __init__(self) -> None:
        super().__init__(
            language="javascript",
            display_name="HTML/CSS/JavaScript",
            screenshot_mode="browser",
        )

    def prompt_rules(self) -> str:
        return """- ОБЯЗАТЕЛЬНО три отдельных файла с полным кодом:
  html/index.html, css/style.css, js/script.js (не описание, не один файл)
- HTML — ТОЛЬКО интерфейс приложения по заданию (форма, кнопки, результаты)
- ЗАПРЕЩЕНО в HTML/CSS/JS: «Цель работы», «Теоретические сведения», текст лабораторной, формулировка задания, поясняющие абзацы вместо кода
- Для форм: валидация HTML5 + JavaScript, localStorage, при отправке — window.open или html/result.html
- html/result.html: страница результатов; при открытии без localStorage — демо-значения полей из варианта
- Не включай ФИО, группу, преподавателя
- Не включай бинарные .png в files"""

    def sanitize_files(self, files: dict[str, str]) -> dict[str, str]:
        return apply_source_sanitize(files)

    def json_example(self) -> str:
        return """{
  "entry_file": "html/index.html",
  "files": {
    "html/index.html": "<!DOCTYPE html>\\n<html>...</html>",
    "css/style.css": "/* стили */",
    "js/script.js": "// логика форм"
  },
  "run_hint": "Открыть html/index.html в браузере"
}"""

    def default_listing_file(self) -> str:
        return "html/index.html"

    def validate_files(self, files: dict[str, str]) -> dict[str, str]:
        return validate_javascript_files(files)

    def needs_generation_retry(self, files: dict[str, str]) -> bool:
        return bool(files) and not javascript_project_complete(files)

    def retry_note(self) -> str:
        return CODER_WEB_RETRY_NOTE

    def resolve_after_llm(
        self,
        data: dict,
        *,
        llm,
        prompt: str,
        entry: str,
    ) -> tuple[dict[str, str], list[str], str]:
        logs: list[str] = []
        files = self.validate_files(data.get("files") or {})
        entry = str(data.get("entry_file") or entry).strip()

        if files and self.needs_generation_retry(files):
            missing = ", ".join(missing_web_parts(files))
            logs.append(f"Web: неполный проект ({missing}), повторный запрос")
            retry_raw = llm_text(llm, prompt + self.retry_note())
            retry_data = parse_json_from_llm(retry_raw) or {}
            retry_files = self.validate_files(retry_data.get("files") or {})
            if retry_files:
                files = retry_files
                entry = str(retry_data.get("entry_file") or entry).strip()
                logs.append("Web: повторная генерация успешна")
            else:
                logs.append("Web: повтор не удался, использованы частичные файлы")

        return self.validate_files(files), logs, entry

    def run(self, project_name: str, files: dict[str, str], *, entry_file: str = "") -> tuple[bool, str]:
        return run_web(project_name, files)


TOOLKIT = WebToolkit()
