"""Assemble agent team from analyzer output (task → agents mapping)."""

from __future__ import annotations

from typing import Any

from backend.domain.workflow.custom_pipeline import (
    CUSTOMIZABLE_NODES,
    custom_pipeline_flags,
    normalize_custom_pipeline,
    validate_custom_pipeline,
)
from backend.domain.workflow.work_profile import analysis_flags, normalize_work_kind

_AGENT_LABELS: dict[str, str] = {
    "analyzer": "Planner",
    "project_init": "ProjectInit",
    "researcher": "Researcher",
    "writer": "Writer",
    "bibliography_verifier": "Bibliography",
    "style_polisher": "StylePolisher",
    "coder_gen": "CoderGen",
    "code_runner": "CodeRunner",
    "diagrammer": "Diagrammer",
    "assets_builder": "Assets",
    "antiplagiat": "Antiplagiat",
    "annex_builder": "Annex",
    "docx_builder": "Formatter",
    "critiquer": "Reviewer",
}

_CORE_TAIL: tuple[str, ...] = ("writer", "style_polisher", "docx_builder", "critiquer")


def _insert_quality_nodes(pipeline: list[str], flags: dict[str, bool]) -> list[str]:
    """Insert bibliography_verifier + style_polisher after writer when appropriate."""
    if "writer" not in pipeline:
        return pipeline

    result = list(pipeline)
    writer_idx = result.index("writer")
    insert_at = writer_idx + 1

    if flags.get("needs_research") and flags.get("enable_bibliography_verifier", True):
        if "bibliography_verifier" not in result:
            result.insert(insert_at, "bibliography_verifier")
            insert_at += 1

    if flags.get("enable_style_polisher", True) and "style_polisher" not in result:
        result.insert(insert_at, "style_polisher")

    if "docx_builder" in result and "style_polisher" in result:
        sp_idx = result.index("style_polisher")
        docx_idx = result.index("docx_builder")
        if sp_idx > docx_idx:
            result.remove("style_polisher")
            result.insert(docx_idx, "style_polisher")

    return result


def _pipeline_from_flags(data: dict[str, Any], work_type: str) -> list[str]:
    """Rule-based pipeline — only explicit analyzer flags, no lab/coursework guesses."""
    flags = analysis_flags(data)
    pipeline: list[str] = ["analyzer"]

    if flags["needs_project_init"]:
        pipeline.append("project_init")

    if flags["needs_research"]:
        pipeline.append("researcher")

    pipeline.append("writer")
    pipeline = _insert_quality_nodes(pipeline, flags)

    if flags["needs_code"]:
        pipeline.extend(["coder_gen", "code_runner"])

    if flags["needs_diagrams"]:
        pipeline.append("diagrammer")

    if flags["needs_excel"] or flags["needs_charts"]:
        pipeline.append("assets_builder")

    if flags["needs_diagrams"] or flags["needs_excel"] or flags["needs_charts"]:
        pipeline.append("antiplagiat")
        pipeline.append("annex_builder")

    pipeline.extend(["docx_builder", "critiquer"])
    return normalize_custom_pipeline(pipeline)


def _agent_from_task_item(item: dict[str, Any]) -> str | None:
    raw = str(item.get("agent") or item.get("agent_id") or "").strip()
    if raw in CUSTOMIZABLE_NODES:
        return raw
    lowered = raw.lower()
    aliases = {
        "planner": "analyzer",
        "plan": "analyzer",
        "research": "researcher",
        "write": "writer",
        "bibliography": "bibliography_verifier",
        "bib": "bibliography_verifier",
        "style": "style_polisher",
        "polish": "style_polisher",
        "code": "coder_gen",
        "runner": "code_runner",
        "diagram": "diagrammer",
        "format": "docx_builder",
        "docx": "docx_builder",
        "review": "critiquer",
        "critique": "critiquer",
        "assets": "assets_builder",
        "excel": "assets_builder",
        "antiplag": "antiplagiat",
        "antiplagiat": "antiplagiat",
        "annex": "annex_builder",
        "appendices": "annex_builder",
        "приложения": "annex_builder",
        "project": "project_init",
    }
    return aliases.get(lowered)


def _ensure_core_pipeline(pipeline: list[str]) -> list[str]:
    result = list(pipeline)
    if "analyzer" not in result:
        result.insert(0, "analyzer")
    for node in _CORE_TAIL:
        if node not in result:
            result.append(node)
    return normalize_custom_pipeline(result)


def _pipeline_from_breakdown(
    breakdown: list[dict[str, Any]],
    data: dict[str, Any],
    work_type: str,
) -> list[str]:
    pipeline: list[str] = ["analyzer"]
    for item in breakdown:
        if not isinstance(item, dict):
            continue
        agent = _agent_from_task_item(item)
        if agent and agent not in pipeline:
            pipeline.append(agent)

    pipeline = _ensure_core_pipeline(pipeline)
    flags = analysis_flags(data)
    pipeline = _insert_quality_nodes(pipeline, flags)

    if flags["needs_code"]:
        for node in ("coder_gen", "code_runner"):
            if node not in pipeline:
                idx = pipeline.index("writer") + 1 if "writer" in pipeline else len(pipeline)
                pipeline.insert(idx, node)
    elif "coder_gen" in pipeline or "code_runner" in pipeline:
        pipeline = [n for n in pipeline if n not in ("coder_gen", "code_runner")]

    if flags["needs_project_init"] and "project_init" not in pipeline:
        pipeline.insert(1, "project_init")
    elif not flags["needs_project_init"] and "project_init" in pipeline:
        pipeline = [n for n in pipeline if n != "project_init"]

    if flags["needs_diagrams"] and "diagrammer" not in pipeline:
        writer_idx = pipeline.index("writer") if "writer" in pipeline else len(pipeline) - 2
        pipeline.insert(writer_idx + 1, "diagrammer")

    if (flags["needs_excel"] or flags["needs_charts"]) and "assets_builder" not in pipeline:
        docx_idx = pipeline.index("docx_builder") if "docx_builder" in pipeline else len(pipeline)
        pipeline.insert(docx_idx, "assets_builder")

    needs_annex = flags["needs_diagrams"] or flags["needs_excel"] or flags["needs_charts"]
    if needs_annex and "antiplagiat" not in pipeline:
        docx_idx = pipeline.index("docx_builder") if "docx_builder" in pipeline else len(pipeline)
        pipeline.insert(docx_idx, "antiplagiat")
    if needs_annex and "annex_builder" not in pipeline:
        docx_idx = pipeline.index("docx_builder") if "docx_builder" in pipeline else len(pipeline)
        pipeline.insert(docx_idx, "annex_builder")

    if flags["needs_research"] and "researcher" not in pipeline:
        analyzer_idx = pipeline.index("analyzer")
        pipeline.insert(analyzer_idx + 1, "researcher")

    return normalize_custom_pipeline(pipeline)


def _default_rationale(pipeline: list[str], data: dict[str, Any]) -> str:
    parts = [_AGENT_LABELS.get(node, node) for node in pipeline if node != "analyzer"]
    topic = data.get("topic") or "работа"
    kind = normalize_work_kind(data.get("detected_work_kind"))
    discipline = data.get("discipline") or "general"
    return (
        f"Для «{topic}» ({kind}, {discipline}) собрана команда: {', '.join(parts)}. "
        "Состав основан на анализе материалов — лишние агенты не добавляются."
    )


def assemble_team_from_analysis(
    data: dict[str, Any],
    *,
    work_type: str = "auto",
) -> tuple[list[str], str, list[dict[str, Any]]]:
    """Return (pipeline, rationale, task_breakdown)."""
    breakdown_raw = data.get("task_breakdown") or []
    breakdown = [item for item in breakdown_raw if isinstance(item, dict)]

    if breakdown:
        pipeline = _pipeline_from_breakdown(breakdown, data, work_type)
    else:
        pipeline = _pipeline_from_flags(data, work_type)
        breakdown = _synthetic_breakdown(pipeline, data)

    rationale = str(data.get("team_rationale") or "").strip() or _default_rationale(pipeline, data)
    errors = validate_custom_pipeline(pipeline)
    if errors:
        pipeline = _pipeline_from_flags(data, work_type)
        rationale = _default_rationale(pipeline, data) + " (упрощённый состав после проверки)"

    return pipeline, rationale, breakdown


def _synthetic_breakdown(pipeline: list[str], data: dict[str, Any]) -> list[dict[str, Any]]:
    """Human-readable steps when LLM did not return task_breakdown."""
    tasks: list[dict[str, Any]] = [
        {
            "task": "Разобрать все загруженные материалы",
            "deliverable": "Требования, тема, тип работы",
            "agent": "analyzer",
        }
    ]
    if "project_init" in pipeline:
        tasks.append(
            {
                "task": "Создать каркас проекта (если нужен код/приложение)",
                "deliverable": "Папка проекта",
                "agent": "project_init",
            }
        )
    if "researcher" in pipeline:
        tasks.append(
            {
                "task": "Найти теорию и источники",
                "deliverable": "Список источников и выжимка",
                "agent": "researcher",
            }
        )
    if "writer" in pipeline:
        tasks.append(
            {
                "task": "Написать текст работы по структуре",
                "deliverable": "Черновик разделов",
                "agent": "writer",
            }
        )
    if "bibliography_verifier" in pipeline:
        tasks.append(
            {
                "task": "Проверить DOI и список литературы",
                "deliverable": "Исправленные источники [1]…[N]",
                "agent": "bibliography_verifier",
            }
        )
    if "style_polisher" in pipeline:
        tasks.append(
            {
                "task": "Убрать шаблонные AI-фразы из текста",
                "deliverable": "Отполированный академический стиль",
                "agent": "style_polisher",
            }
        )
    if "coder_gen" in pipeline:
        tasks.append(
            {
                "task": f"Сгенерировать код ({data.get('code_language', 'python')})",
                "deliverable": "Исходники",
                "agent": "coder_gen",
            }
        )
    if "code_runner" in pipeline:
        tasks.append(
            {
                "task": "Запустить и проверить программу",
                "deliverable": "Лог выполнения, скриншоты",
                "agent": "code_runner",
            }
        )
    if "diagrammer" in pipeline:
        tasks.append(
            {
                "task": "Построить диаграммы (UML / IDEF0 / блок-схемы)",
                "deliverable": "Файлы диаграмм",
                "agent": "diagrammer",
            }
        )
    if "assets_builder" in pipeline:
        tasks.append(
            {
                "task": "Подготовить таблицы Excel и графики",
                "deliverable": "Таблицы и charts",
                "agent": "assets_builder",
            }
        )
    if "antiplagiat" in pipeline:
        tasks.append(
            {
                "task": "Подготовить заявление об оригинальности и скриншот Антиплагиат",
                "deliverable": "originality_pct + скриншот",
                "agent": "antiplagiat",
            }
        )
    if "annex_builder" in pipeline:
        tasks.append(
            {
                "task": "Спланировать приложения (буквы, подписи)",
                "deliverable": "План приложений",
                "agent": "annex_builder",
            }
        )
    if "docx_builder" in pipeline:
        tasks.append(
            {
                "task": "Собрать docx по ГОСТ / СТП",
                "deliverable": "Файл отчёта",
                "agent": "docx_builder",
            }
        )
    if "critiquer" in pipeline:
        tasks.append(
            {
                "task": "Проверить качество и соответствие требованиям",
                "deliverable": "Замечания и правки",
                "agent": "critiquer",
            }
        )
    return tasks


def apply_team_approval_answer(
    *,
    default_pipeline: list[str],
    answer: Any,
) -> dict[str, Any]:
    """Merge user approval / pipeline edits after team HITL interrupt."""
    pipeline = list(default_pipeline)
    if isinstance(answer, dict):
        if answer.get("custom_pipeline"):
            pipeline = normalize_custom_pipeline(answer["custom_pipeline"])
        elif answer.get("pipeline"):
            pipeline = normalize_custom_pipeline(answer["pipeline"])

    flags = custom_pipeline_flags(pipeline)
    return {
        "custom_pipeline": pipeline,
        "user_defined_pipeline": True,
        "awaiting_team_approval": False,
        "needs_code": flags["needs_code"],
        "needs_diagrams": flags["needs_diagrams"],
        "needs_excel": flags["needs_excel"],
        "needs_charts": flags["needs_charts"],
        "needs_annexes": flags.get("needs_annexes", "annex_builder" in pipeline),
        "needs_antiplagiat": flags.get("needs_antiplagiat", "antiplagiat" in pipeline),
        "needs_project_init": "project_init" in pipeline,
    }


def build_team_interrupt_payload(
    *,
    pipeline: list[str],
    rationale: str,
    task_breakdown: list[dict[str, Any]],
    topic: str,
    detected_work_kind: str = "",
    discipline: str = "",
    structure_outline: str = "",
    work_brief_summary: str = "",
    structure_source: str = "",
) -> dict[str, Any]:
    return {
        "type": "team_approval",
        "topic": topic,
        "detected_work_kind": detected_work_kind,
        "discipline": discipline,
        "pipeline": pipeline,
        "rationale": rationale,
        "task_breakdown": task_breakdown,
        "structure_outline": structure_outline,
        "work_brief_summary": work_brief_summary,
        "structure_source": structure_source,
        "agents": [
            {"id": node, "label": _AGENT_LABELS.get(node, node)}
            for node in pipeline
            if node in CUSTOMIZABLE_NODES
        ],
    }
