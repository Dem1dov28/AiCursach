"""ProjectInit — однократное создание каркаса проекта."""

from __future__ import annotations

from backend.core.paths import prune_lab_extras
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import init_project
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm


def project_init_node(state: WorkState) -> dict:
    if state.get("project_initialized"):
        return {}

    project_name = state.get("project_name", "WorkProject")
    work_type = state.get("work_type", "lab")
    ok, msg, proj_path = init_project(project_name, work_type=work_type)
    if work_type == "lab" and ok:
        prune_lab_extras(proj_path)

    result = {
        "project_initialized": ok,
        "project_path": str(proj_path),
        "tool_log": [msg if ok else f"Ошибка init_project: {msg}"],
    }
    result.update(gate_after_llm(state, "project_init", {}))
    return result
