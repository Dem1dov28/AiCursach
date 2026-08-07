"""CoderGen — LLM-генерация исходного кода (без запуска)."""

from __future__ import annotations

import json

from backend.infrastructure.langgraph.nodes.coder_helpers import (
    language_prompt_rules,
    resolve_code_files,
)
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import CODER_PROMPT
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.code_language import normalize_code_language
from backend.infrastructure.adapters.code_tools import get_code_toolkit
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm


def coder_gen_node(state: WorkState) -> dict:
    language = normalize_code_language(state.get("code_language", "python"))
    toolkit = get_code_toolkit(language)
    llm = get_llm()
    prompt = CODER_PROMPT.format(
        topic=state.get("topic", ""),
        code_language=toolkit.display_name,
        requirements=state.get("requirements", ""),
        general_requirements_text=(
            state.get("general_requirements_text") or state.get("assignment_text") or ""
        )[:3000],
        variant_task_text=(
            state.get("variant_task_text") or state.get("assignment_text") or ""
        )[:4000],
        json_example=toolkit.json_example(),
        language_rules=language_prompt_rules(language),
    )
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {}
    files, gen_logs, entry = resolve_code_files(data, state, language, llm, prompt)

    if not files:
        attempts = int(state.get("coder_gen_attempts") or 0) + 1
        result = {
            "code_generated": False,
            "code_run_done": False,
            "code_run_success": False,
            "code_run_output": "CoderGen не сгенерировал файлы",
            "coder_gen_attempts": attempts,
            "tool_log": gen_logs or ["CoderGen: пустой результат"],
        }
        result.update(gate_after_llm(state, "coder_gen", data))
        return result

    files = toolkit.sanitize_files(files)

    result = {
        "code_generated": True,
        "code_run_done": False,
        "coder_gen_attempts": 0,
        "code_files": json.dumps(files, ensure_ascii=False),
        "code_entry_file": entry,
        "tool_log": [
            f"CoderGen [{toolkit.display_name}]: подготовлено {len(files)} файлов",
            *gen_logs,
        ],
    }
    result.update(gate_after_llm(state, "coder_gen", data))
    return result
