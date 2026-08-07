"""CodeRunner — запись и выполнение сгенерированного кода."""

from __future__ import annotations

import json

from backend.infrastructure.langgraph.nodes.coder_helpers import merge_code_into_draft
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.code_language import normalize_code_language
from backend.infrastructure.adapters.code_runner import run_code, write_code_files
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm


def code_runner_node(state: WorkState) -> dict:
    project_name = state.get("project_name", "WorkProject")
    language = normalize_code_language(state.get("code_language", "python"))
    raw_files = state.get("code_files", "")
    try:
        files = json.loads(raw_files) if raw_files else {}
    except json.JSONDecodeError:
        files = {}

    if not files:
        result = {
            "code_run_done": True,
            "code_run_success": False,
            "code_run_output": "CodeRunner: нет файлов для запуска",
            "tool_log": ["CodeRunner: code_files пуст"],
        }
        result.update(gate_after_llm(state, "code_runner", {}))
        return result

    written = write_code_files(project_name, files)
    entry = state.get("code_entry_file", "")
    ok, output = run_code(
        project_name,
        files,
        language=language,
        entry_file=entry,
    )

    content_update = merge_code_into_draft(
        state.get("content_draft", ""),
        files,
        output,
        ok,
        language=language,
    )

    result = {
        "code_run_done": True,
        "code_run_output": output[:8000],
        "code_run_success": ok,
        "content_draft": content_update,
        "tool_log": [
            f"CodeRunner ({language}): записано {len(written)} файлов в src/",
            f"Запуск: {'успех' if ok else 'ошибка'}",
            output[:500] if output else "(нет вывода)",
        ],
    }
    llm_hint = {
        "confidence": 0.92 if ok else 0.58,
        "needs_clarification": not ok,
        "clarification": None
        if ok
        else {
            "scenario": "ambiguous_task",
            "question": "Программа завершилась с ошибкой. Как поступить?",
            "options": [
                "Перегенерировать код (CoderGen)",
                "Продолжить с текущим кодом и описать ошибку в отчёте",
                "Упростить задание / убрать часть функций",
            ],
        },
    }
    result.update(gate_after_llm(state, "code_runner", llm_hint))
    return result
