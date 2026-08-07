"""AssetsBuilder — Excel и графики для курсовых."""

from __future__ import annotations

from backend.domain.document.asset_package import asset_package_issues, normalize_asset_package
from backend.domain.workflow.work_profile import uses_coursework_docx
from backend.domain.workflow.work_state import WorkState
from backend.infrastructure.adapters.bsuir_tools import parse_json_from_llm
from backend.infrastructure.adapters.coursework_bridge import prepare_coursework_assets
from backend.infrastructure.langgraph.clarification_gate import gate_after_llm
from backend.infrastructure.llm.gateway import get_llm, llm_text
from backend.infrastructure.llm.prompts.templates import ASSETS_DATA_PROMPT


def assets_builder_node(state: WorkState) -> dict:
    project_name = state.get("project_name", "WorkProject")
    coursework = uses_coursework_docx(dict(state))
    logs: list[str] = []
    assets: list[str] = []

    needs_charts = bool(state.get("needs_charts", coursework))
    needs_excel = bool(state.get("needs_excel", coursework))
    needed = needs_charts or needs_excel

    if not (coursework and needed):
        logs.append("AssetsBuilder: skipped (не требуется для данного типа работы)")
        result = {
            "tool_log": logs,
            "coursework_assets_done": True,
            "assets_quality": "skipped",
            "assets_builder_attempts": 0,
            "diagram_files": assets,
        }
        result.update(gate_after_llm(state, "assets_builder", {}))
        return result

    topic = state.get("topic", "") or ""
    requirements = state.get("requirements", "") or ""

    # 1) Specialized IOUZ toolkit when markers + TSV present
    cw_assets, cw_logs, mode = prepare_coursework_assets(
        project_name,
        topic=topic,
        requirements=requirements,
        package=None,
    )
    assets.extend(cw_assets)
    logs.extend(cw_logs)
    llm_payload: dict = {}

    # 2) Topic-driven LLM package → TSV + charts
    if mode != "iouz":
        package, llm_payload, llm_logs = _llm_asset_package(state)
        logs.extend(llm_logs)
        if package:
            topic_assets, topic_logs, mode = prepare_coursework_assets(
                project_name,
                topic=topic,
                requirements=requirements,
                use_iouz=False,
                package=package,
            )
            assets.extend(topic_assets)
            logs.extend(topic_logs)

    attempts = int(state.get("assets_builder_attempts") or 0)

    if mode == "iouz" and assets:
        logs.append("AssetsBuilder: IOUZ toolkit — success")
        result = {
            "tool_log": logs,
            "coursework_assets_done": True,
            "assets_quality": "iouz",
            "assets_builder_attempts": 0,
            "diagram_files": assets,
        }
    elif mode == "topic" and any(str(a).lower().endswith(".png") for a in assets):
        logs.append("AssetsBuilder: topic-driven — success")
        result = {
            "tool_log": logs,
            "coursework_assets_done": True,
            "assets_quality": "topic",
            "assets_builder_attempts": 0,
            "diagram_files": assets,
        }
    else:
        attempts += 1
        logs.append("AssetsBuilder: артефакты не созданы")
        result = {
            "tool_log": logs,
            "coursework_assets_done": False,
            "assets_quality": "failed",
            "assets_builder_attempts": attempts,
            "diagram_files": assets,
        }

    result.update(gate_after_llm(state, "assets_builder", llm_payload))
    return result


def _llm_asset_package(state: WorkState) -> tuple[dict | None, dict, list[str]]:
    logs: list[str] = []
    llm = get_llm(temperature=0.3)
    prompt = ASSETS_DATA_PROMPT.format(
        topic=state.get("topic", "") or "",
        requirements=(state.get("requirements") or "")[:4000],
        structure_outline=(state.get("structure_outline") or "")[:3000],
        content_draft=(state.get("content_draft") or "")[:6000],
    )
    raw = llm_text(llm, prompt)
    data = parse_json_from_llm(raw) or {}
    package = normalize_asset_package(data)
    issues = asset_package_issues(package)
    if issues:
        logs.append("AssetsBuilder LLM: " + "; ".join(issues))
        return None, data if isinstance(data, dict) else {}, logs
    logs.append(f"AssetsBuilder LLM: charts={len(package['charts'])}")
    return package, data if isinstance(data, dict) else {}, logs
