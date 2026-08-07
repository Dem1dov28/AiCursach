"""LangGraph workflow factory — infrastructure layer."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from backend.infrastructure.langgraph.nodes.analyzer import analyzer_node
from backend.infrastructure.langgraph.nodes.annex_builder import annex_builder_node
from backend.infrastructure.langgraph.nodes.antiplagiat import antiplagiat_node
from backend.infrastructure.langgraph.nodes.assets_builder import assets_builder_node
from backend.infrastructure.langgraph.nodes.code_runner_agent import code_runner_node
from backend.infrastructure.langgraph.nodes.coder_gen import coder_gen_node
from backend.infrastructure.langgraph.nodes.critiquer import critiquer_node
from backend.infrastructure.langgraph.nodes.diagrammer import diagrammer_node
from backend.infrastructure.langgraph.nodes.docx_builder import docx_builder_node
from backend.infrastructure.langgraph.nodes.project_init import project_init_node
from backend.infrastructure.langgraph.nodes.researcher import researcher_node
from backend.infrastructure.langgraph.nodes.bibliography_verifier import bibliography_verifier_node
from backend.infrastructure.langgraph.nodes.style_polisher import style_polisher_node
from backend.infrastructure.langgraph.nodes.supervisor import supervisor_node
from backend.infrastructure.langgraph.nodes.writer import writer_node
from backend.infrastructure.langgraph.checkpointer import get_checkpointer
from backend.infrastructure.langgraph.agent_context import agent_scope
from backend.domain.workflow.work_state import WorkState

WORKER_NODES = (
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

HITL_INTERRUPT_NODES = ("writer",)

_workflow_app = None


def _route_supervisor(state: WorkState) -> str:
    step = state.get("next_step", "analyzer")
    if step == "END":
        return "END"
    return step


def _wrap_agent(name: str, node_fn):
    def wrapped(state: WorkState):
        with agent_scope(name):
            return node_fn(state)

    return wrapped


def _build_state_graph() -> StateGraph:
    workflow = StateGraph(WorkState)

    workflow.add_node("supervisor", _wrap_agent("supervisor", supervisor_node))
    workflow.add_node("analyzer", _wrap_agent("analyzer", analyzer_node))
    workflow.add_node("project_init", _wrap_agent("project_init", project_init_node))
    workflow.add_node("researcher", _wrap_agent("researcher", researcher_node))
    workflow.add_node("writer", _wrap_agent("writer", writer_node))
    workflow.add_node(
        "bibliography_verifier",
        _wrap_agent("bibliography_verifier", bibliography_verifier_node),
    )
    workflow.add_node("style_polisher", _wrap_agent("style_polisher", style_polisher_node))
    workflow.add_node("coder_gen", _wrap_agent("coder_gen", coder_gen_node))
    workflow.add_node("code_runner", _wrap_agent("code_runner", code_runner_node))
    workflow.add_node("diagrammer", _wrap_agent("diagrammer", diagrammer_node))
    workflow.add_node("assets_builder", _wrap_agent("assets_builder", assets_builder_node))
    workflow.add_node("antiplagiat", _wrap_agent("antiplagiat", antiplagiat_node))
    workflow.add_node("annex_builder", _wrap_agent("annex_builder", annex_builder_node))
    workflow.add_node("docx_builder", _wrap_agent("docx_builder", docx_builder_node))
    workflow.add_node("critiquer", _wrap_agent("critiquer", critiquer_node))

    workflow.set_entry_point("supervisor")

    for node in WORKER_NODES:
        workflow.add_edge(node, "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        _route_supervisor,
        {node: node for node in WORKER_NODES} | {"END": END},
    )
    return workflow


def compile_workflow(*, enable_hitl: bool = True):
    kwargs: dict = {"checkpointer": get_checkpointer()}
    if enable_hitl:
        kwargs["interrupt_before"] = list(HITL_INTERRUPT_NODES)
    return _build_state_graph().compile(**kwargs)


def get_workflow_app():
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = compile_workflow(enable_hitl=True)
    return _workflow_app


def reset_workflow_app() -> None:
    global _workflow_app
    _workflow_app = None


class _LazyWorkflow:
    def stream(self, *args, **kwargs):
        return get_workflow_app().stream(*args, **kwargs)

    def update_state(self, *args, **kwargs):
        return get_workflow_app().update_state(*args, **kwargs)

    def get_state(self, *args, **kwargs):
        return get_workflow_app().get_state(*args, **kwargs)


app = _LazyWorkflow()
