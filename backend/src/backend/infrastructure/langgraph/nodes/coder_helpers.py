"""Общие функции генерации кода для coder_gen и code_runner."""

from __future__ import annotations

import json

from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.code_tools import get_code_toolkit
from backend.infrastructure.adapters.code_tools.web_toolkit import WebToolkit
from backend.infrastructure.adapters.lab_code import is_code_listing


def resolve_code_files(
    data: dict,
    state: WorkState,
    language: str,
    llm,
    prompt: str,
) -> tuple[dict[str, str], list[str], str]:
    """Сгенерированные файлы, логи и entry_file через языковой инструмент."""
    toolkit = get_code_toolkit(language)
    logs: list[str] = []
    entry = str(data.get("entry_file") or "").strip()
    files = toolkit.validate_files(data.get("files") or {})

    if not files:
        files = files_from_draft_code(state, toolkit)
        if files:
            logs.append("Coder: взяты файлы из черновика с листингом")

    if isinstance(toolkit, WebToolkit):
        files, web_logs, entry = toolkit.resolve_after_llm(
            {"files": files, "entry_file": entry},
            llm=llm,
            prompt=prompt,
            entry=entry,
        )
        logs.extend(web_logs)
    else:
        files = toolkit.validate_files(files)

    return files, logs, entry


def files_from_draft_code(state: WorkState, toolkit) -> dict[str, str]:
    draft_raw = state.get("content_draft", "")
    if not draft_raw:
        return {}
    try:
        draft = json.loads(draft_raw)
    except json.JSONDecodeError:
        return {}
    code = str(draft.get("program_code") or "").strip()
    if not is_code_listing(code):
        return {}
    files = listing_to_files(code)
    return toolkit.validate_files(files) if files else {}


def listing_to_files(listing: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for block in listing.split("// === "):
        block = block.strip()
        if not block:
            continue
        header, _, body = block.partition("\n")
        name = header.replace("===", "").strip()
        if name and body.strip():
            files[name] = body.strip()
    return files


def coder_json_example(language: str) -> str:
    return get_code_toolkit(language).json_example()


def language_prompt_rules(language: str) -> str:
    return get_code_toolkit(language).prompt_rules()


def merge_code_into_draft(
    draft: str,
    files: dict[str, str],
    run_output: str,
    success: bool,
    *,
    language: str = "",
) -> str:
    try:
        data = json.loads(draft) if draft.strip() else {}
    except json.JSONDecodeError:
        data = {}

    if not isinstance(data, dict):
        data = {}

    toolkit = get_code_toolkit(language)
    data["_code_language"] = toolkit.language
    data["program_code"] = format_code_listing(files)
    work = (
        "Программа реализована и протестирована. "
        f"{'Успешно' if success else 'С ошибками при запуске'}.\n"
    )
    if success and toolkit.screenshot_mode == "browser":
        work += (
            "Приложение представляет собой HTML-страницу с CSS и JavaScript. "
            "Ниже приведены скриншоты экранных форм."
        )
    elif success and run_output:
        work += f"Вывод программы:\n{run_output[:2000]}"
    elif not success:
        work += (
            "Запуск завершился с ошибкой; скриншот консоли в отчёт не включается. "
            "Исправьте код в папке src/."
        )
    data["program_work"] = work
    data.pop("_code_language", None)
    return json.dumps(data, ensure_ascii=False, indent=2)


def format_code_listing(files: dict[str, str]) -> str:
    parts: list[str] = []
    for name, content in files.items():
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            continue
        if not isinstance(content, str):
            continue
        parts.append(f"// === {name} ===\n{content.strip()}")
    return "\n\n".join(parts)
