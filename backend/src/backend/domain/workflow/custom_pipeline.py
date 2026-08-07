"""Custom agent pipeline — validation and routing for blank-canvas jobs."""

from __future__ import annotations

from typing import Callable

from backend.domain.workflow.revision_limit import effective_max_revisions
from backend.domain.workflow.rerun import normalize_revision_target
from backend.domain.workflow.work_state import WorkState

CUSTOMIZABLE_NODES: tuple[str, ...] = (
    "analyzer",
    "project_init",
    "researcher",
    "writer",
    "bibliography_verifier",
    "style_polisher",
    "coder_gen",
    "code_runner",
    "diagrammer",
    "assets_builder",
    "antiplagiat",
    "annex_builder",
    "docx_builder",
    "critiquer",
)

MAX_CODER_GEN_ATTEMPTS = 2
MAX_QUALITY_ATTEMPTS = 2
MAX_ARTIFACT_ATTEMPTS = 2


def _coder_gen_done(state: WorkState) -> bool:
    if state.get("code_generated"):
        return True
    return int(state.get("coder_gen_attempts") or 0) >= MAX_CODER_GEN_ATTEMPTS


def _bibliography_done(state: WorkState) -> bool:
    if not state.get("enable_bibliography_verifier", True):
        return True
    if state.get("bibliography_verified"):
        return True
    return int(state.get("bibliography_attempts") or 0) >= MAX_QUALITY_ATTEMPTS


def _style_done(state: WorkState) -> bool:
    if not state.get("enable_style_polisher", True):
        return True
    if state.get("style_polished"):
        return True
    return int(state.get("style_polisher_attempts") or 0) >= MAX_QUALITY_ATTEMPTS


def _diagrammer_done(state: WorkState) -> bool:
    if state.get("diagrams_generated"):
        return True
    return int(state.get("diagrammer_attempts") or 0) >= MAX_ARTIFACT_ATTEMPTS


def _assets_done(state: WorkState) -> bool:
    if state.get("coursework_assets_done"):
        return True
    return int(state.get("assets_builder_attempts") or 0) >= MAX_ARTIFACT_ATTEMPTS


def _annex_done(state: WorkState) -> bool:
    if state.get("annex_plan_done"):
        return True
    return int(state.get("annex_builder_attempts") or 0) >= MAX_ARTIFACT_ATTEMPTS


def _antiplagiat_done(state: WorkState) -> bool:
    if state.get("antiplagiat_done"):
        return True
    return int(state.get("antiplagiat_attempts") or 0) >= MAX_ARTIFACT_ATTEMPTS


_NODE_DONE: dict[str, Callable[[WorkState], bool]] = {
    "analyzer": lambda s: bool(s.get("requirements")),
    "project_init": lambda s: bool(s.get("project_initialized")),
    "researcher": lambda s: bool(s.get("research_findings")),
    "writer": lambda s: bool(s.get("content_draft", "").strip()),
    "bibliography_verifier": _bibliography_done,
    "style_polisher": _style_done,
    "coder_gen": _coder_gen_done,
    "code_runner": lambda s: bool(s.get("code_run_done")),
    "diagrammer": _diagrammer_done,
    "assets_builder": _assets_done,
    "antiplagiat": _antiplagiat_done,
    "annex_builder": _annex_done,
    "docx_builder": lambda s: bool(s.get("output_docx_path")),
    "critiquer": lambda s: bool(s.get("critique_notes")),
}


def normalize_custom_pipeline(raw: list[str] | tuple[str, ...] | None) -> list[str]:
    if not raw:
        return []
    seen: set[str] = set()
    pipeline: list[str] = []
    for item in raw:
        node = str(item).strip()
        if node not in CUSTOMIZABLE_NODES or node in seen:
            continue
        seen.add(node)
        pipeline.append(node)
    return pipeline


def validate_custom_pipeline(pipeline: list[str]) -> list[str]:
    errors: list[str] = []
    if len(pipeline) < 2:
        errors.append("Добавьте минимум два агента (например, Planner и Writer).")
    if "analyzer" not in pipeline:
        errors.append("В графе должен быть Planner (analyzer) — разбор задания.")
    if "writer" not in pipeline:
        errors.append("В графе должен быть Writer — генерация текста.")
    unknown = [node for node in pipeline if node not in CUSTOMIZABLE_NODES]
    if unknown:
        errors.append(f"Неизвестные агенты: {', '.join(unknown)}")
    return errors


def pipeline_from_graph_edges(
    *,
    node_ids: list[str],
    edges: list[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    """Build execution order from supervisor-rooted flow edges."""
    errors: list[str] = []
    allowed = set(CUSTOMIZABLE_NODES)
    workers = [node for node in node_ids if node in allowed]
    if not workers:
        return [], ["Добавьте хотя бы одного агента на холст."]

    flow_edges = [(src, tgt) for src, tgt in edges if not (src == "critiquer" and tgt == "writer")]
    loop_present = any(src == "critiquer" and tgt == "writer" for src, tgt in edges)

    adjacency: dict[str, list[str]] = {node: [] for node in ["supervisor", *workers]}
    for src, tgt in flow_edges:
        if src in adjacency and tgt in adjacency:
            adjacency[src].append(tgt)

    order: list[str] = []
    visited: set[str] = set()
    current = "supervisor"
    while True:
        next_nodes = [node for node in adjacency.get(current, []) if node not in visited]
        if len(next_nodes) > 1:
            errors.append("Граф должен быть линейным — у каждого шага не более одного следующего агента.")
            break
        if not next_nodes:
            break
        nxt = next_nodes[0]
        if nxt in visited:
            errors.append("В графе обнаружен цикл (кроме Reviewer → Writer).")
            break
        visited.add(nxt)
        if nxt in allowed:
            order.append(nxt)
        current = nxt

    missing = [node for node in workers if node not in order]
    if missing:
        errors.append(
            "Не все агенты связаны с Supervisor: "
            + ", ".join(missing)
            + ". Соедините их стрелками от координатора."
        )

    if loop_present:
        if "critiquer" not in order or "writer" not in order:
            errors.append("Цикл правок возможен только между Reviewer и Writer.")
        elif order.index("critiquer") <= order.index("writer"):
            errors.append("Reviewer должен идти после Writer в основной цепочке.")

    validation = validate_custom_pipeline(order)
    return order, errors + validation


def custom_supervisor_next(state: WorkState) -> dict:
    """Return supervisor patch for work_type=custom."""
    pipeline = normalize_custom_pipeline(state.get("custom_pipeline"))
    if not pipeline:
        return {"next_step": "END", "current_sub_task": "Пустой пайплайн — завершение"}

    critique = state.get("critique_notes", "")
    revision = int(state.get("revision_number") or 0)
    max_revisions = effective_max_revisions(state)
    has_build = bool(state.get("output_docx_path"))

    if "APPROVED" in critique.upper() and (
        not has_build or "docx_builder" not in pipeline or "critiquer" not in pipeline
    ):
        return {"next_step": "END", "current_sub_task": "Работа завершена"}

    if (
        "critiquer" in pipeline
        and "writer" in pipeline
        and critique
        and "APPROVED" not in critique.upper()
        and revision < max_revisions
    ):
        critiquer_done = _NODE_DONE["critiquer"](state)
        writer_done = _NODE_DONE["writer"](state)
        if critiquer_done and writer_done:
            target = normalize_revision_target(state.get("critique_rerun") or "writer")
            if target not in pipeline:
                target = "writer"
            patch: dict = {
                "next_step": target,
                "revision_number": revision + 1,
                "current_sub_task": "Доработка по замечаниям Reviewer",
                "critique_rerun": "",
                "output_docx_path": "",
            }
            if target in ("writer", "bibliography_verifier", "style_polisher"):
                patch["bibliography_verified"] = False
                patch["style_polished"] = False
                patch["bibliography_attempts"] = 0
                patch["style_polisher_attempts"] = 0
            if target == "diagrammer":
                patch["diagrams_generated"] = False
                patch["diagrammer_attempts"] = 0
            if target == "assets_builder":
                patch["coursework_assets_done"] = False
                patch["assets_builder_attempts"] = 0
                patch["assets_quality"] = ""
            if target == "annex_builder":
                patch["annex_plan_done"] = False
                patch["annex_builder_attempts"] = 0
                patch["annex_plan"] = ""
            if target == "antiplagiat":
                patch["antiplagiat_done"] = False
                patch["antiplagiat_attempts"] = 0
                patch["antiplagiat_screenshot"] = ""
                patch["annex_reserved_letters"] = []
            if target == "coder_gen":
                patch["code_generated"] = False
                patch["code_run_done"] = False
                patch["coder_gen_attempts"] = 0
            return patch

    if revision >= max_revisions and critique and "APPROVED" not in critique.upper():
        return {"next_step": "END", "current_sub_task": "Достигнут лимит ревизий — финализация"}

    for node in pipeline:
        if not _NODE_DONE[node](state):
            labels = {
                "analyzer": "Разобрать задание",
                "project_init": "Создать каркас проекта",
                "researcher": "Найти источники",
                "writer": "Сгенерировать текст",
                "bibliography_verifier": "Проверить список источников",
                "style_polisher": "Убрать AI-клише из текста",
                "coder_gen": "Сгенерировать код",
                "code_runner": "Запустить код",
                "diagrammer": "Сгенерировать диаграммы",
                "assets_builder": "Подготовить Excel и графики",
                "antiplagiat": "Антиплагиат / оригинальность",
                "annex_builder": "Спланировать приложения",
                "docx_builder": "Собрать docx",
                "critiquer": "Проверить качество",
            }
            return {"next_step": node, "current_sub_task": labels.get(node, node)}

    if "critiquer" in pipeline and not critique:
        return {"next_step": "critiquer", "current_sub_task": "Проверить качество"}

    if "critiquer" in pipeline and "APPROVED" in critique.upper():
        return {"next_step": "END", "current_sub_task": "Работа одобрена Reviewer"}

    return {"next_step": "END", "current_sub_task": "Пайплайн выполнен"}


def custom_pipeline_flags(pipeline: list[str]) -> dict[str, bool]:
    """Derive needs_* flags from selected nodes."""
    nodes = set(pipeline)
    return {
        "needs_code": "coder_gen" in nodes or "code_runner" in nodes,
        "needs_diagrams": "diagrammer" in nodes,
        "needs_excel": "assets_builder" in nodes,
        "needs_charts": "assets_builder" in nodes,
        "needs_annexes": "annex_builder" in nodes,
        "needs_antiplagiat": "antiplagiat" in nodes,
    }
