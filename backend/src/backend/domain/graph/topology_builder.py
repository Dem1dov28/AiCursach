"""Pure builder for workflow graph topology (UI view, decoupled from LangGraph)."""

from __future__ import annotations

from backend.domain.graph.entities import GraphEdge, GraphNode, GraphTopology
from backend.domain.workflow.custom_pipeline import CUSTOMIZABLE_NODES, normalize_custom_pipeline

_NODE_META: dict[str, tuple[str, str]] = {
    "supervisor": ("Supervisor", "Маршрутизация workflow"),
    "analyzer": ("Planner", "План и структура глав"),
    "project_init": ("ProjectInit", "Каркас проекта"),
    "researcher": ("Researcher", "Поиск источников и теории"),
    "writer": ("Writer", "Генерация текста"),
    "bibliography_verifier": ("Bibliography", "Проверка источников и DOI"),
    "style_polisher": ("StylePolisher", "Академическая полировка текста"),
    "critiquer": ("Reviewer", "Проверка и правки"),
    "coder_gen": ("CoderGen", "Генерация кода"),
    "code_runner": ("CodeRunner", "Запуск и проверка кода"),
    "diagrammer": ("Diagrammer", "Диаграммы UML / IDEF0"),
    "assets_builder": ("Assets", "Excel и графики"),
    "antiplagiat": ("Antiplagiat", "Оригинальность / скриншот"),
    "annex_builder": ("Annex", "План приложений"),
    "docx_builder": ("Formatter", "ГОСТ / сборка docx"),
}

# Typical execution order (each step returns to supervisor in LangGraph; shown as pipeline).
_LAB_PIPELINE: tuple[str, ...] = (
    "supervisor",
    "analyzer",
    "project_init",
    "researcher",
    "writer",
    "bibliography_verifier",
    "style_polisher",
    "coder_gen",
    "code_runner",
    "diagrammer",
    "docx_builder",
    "critiquer",
)

_COURSEWORK_PIPELINE: tuple[str, ...] = (
    "supervisor",
    "analyzer",
    "researcher",
    "writer",
    "bibliography_verifier",
    "style_polisher",
    "diagrammer",
    "assets_builder",
    "antiplagiat",
    "annex_builder",
    "docx_builder",
    "critiquer",
)

_FULL_PIPELINE: tuple[str, ...] = (
    "supervisor",
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


def _pipeline_for(work_type: str, custom_pipeline: list[str] | None = None) -> tuple[str, ...]:
    normalized = (work_type or "full").strip().lower()
    if normalized == "custom":
        pipeline = normalize_custom_pipeline(custom_pipeline or [])
        return ("supervisor", *pipeline)
    if normalized == "coursework":
        return _COURSEWORK_PIPELINE
    if normalized in ("auto", "full"):
        return _FULL_PIPELINE
    if normalized == "lab":
        return _LAB_PIPELINE
    return _FULL_PIPELINE


def _layout_pipeline(node_ids: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    """Vertical pipeline: supervisor on top, workers below."""
    positions: dict[str, tuple[float, float]] = {}
    center_x = 400.0
    top_y = 0.0
    step_y = 120.0

    for index, node_id in enumerate(node_ids):
        positions[node_id] = (center_x, top_y + index * step_y)

    return positions


def _build_edges(node_ids: tuple[str, ...]) -> tuple[GraphEdge, ...]:
    edges: list[GraphEdge] = []
    allowed = set(node_ids)

    for index in range(len(node_ids) - 1):
        source = node_ids[index]
        target = node_ids[index + 1]
        if source not in allowed or target not in allowed:
            continue
        kind = "route" if source == "supervisor" else "flow"
        edges.append(
            GraphEdge(
                id=f"e-{source}-{target}",
                source=source,
                target=target,
                kind=kind,  # type: ignore[arg-type]
                label="",
            )
        )

    if "critiquer" in allowed and "writer" in allowed:
        edges.append(
            GraphEdge(
                id="e-critiquer-writer",
                source="critiquer",
                target="writer",
                kind="loop",
                label="revision",
            )
        )

    return tuple(edges)


def build_graph_topology(
    work_type: str = "full",
    custom_pipeline: list[str] | None = None,
) -> GraphTopology:
    """Return graph topology filtered by work type or custom pipeline."""
    normalized = (work_type or "full").strip().lower()
    pipeline = _pipeline_for(normalized, custom_pipeline)
    layout = _layout_pipeline(pipeline)

    nodes = tuple(
        GraphNode(
            id=node_id,
            label=_NODE_META[node_id][0],
            role=_NODE_META[node_id][1],
            kind="supervisor" if node_id == "supervisor" else "worker",
            position={"x": layout[node_id][0], "y": layout[node_id][1]},
        )
        for node_id in pipeline
        if node_id in _NODE_META
    )

    edges = _build_edges(pipeline)

    return GraphTopology(work_type=normalized, nodes=nodes, edges=edges)


def agent_catalog() -> list[dict[str, str]]:
    """Palette entries for the blank-canvas designer."""
    return [
        {
            "id": node_id,
            "label": _NODE_META[node_id][0],
            "role": _NODE_META[node_id][1],
        }
        for node_id in CUSTOMIZABLE_NODES
        if node_id in _NODE_META
    ]
