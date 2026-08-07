"""Tests for custom pipeline routing and topology."""

from backend.domain.graph.topology_builder import build_graph_topology
from backend.domain.workflow.custom_pipeline import (
    custom_supervisor_next,
    normalize_custom_pipeline,
    pipeline_from_graph_edges,
    validate_custom_pipeline,
)


def test_normalize_custom_pipeline_dedupes():
    pipeline = normalize_custom_pipeline(["writer", "analyzer", "writer", "unknown"])
    assert pipeline == ["writer", "analyzer"]


def test_validate_custom_pipeline_requires_core_nodes():
    errors = validate_custom_pipeline(["researcher"])
    assert any("Planner" in err for err in errors)
    assert any("Writer" in err for err in errors)


def test_custom_topology_from_pipeline():
    pipeline = ["analyzer", "writer", "critiquer"]
    topology = build_graph_topology("custom", custom_pipeline=pipeline)
    node_ids = [node.id for node in topology.nodes]
    assert node_ids[0] == "supervisor"
    assert node_ids[1:] == pipeline
    loop_edges = [edge for edge in topology.edges if edge.kind == "loop"]
    assert any(edge.source == "critiquer" and edge.target == "writer" for edge in loop_edges)


def test_pipeline_from_graph_edges_linear_chain():
    pipeline, errors = pipeline_from_graph_edges(
        node_ids=["analyzer", "writer", "critiquer"],
        edges=[
            ("supervisor", "analyzer"),
            ("analyzer", "writer"),
            ("writer", "critiquer"),
            ("critiquer", "writer"),
        ],
    )
    assert not errors
    assert pipeline == ["analyzer", "writer", "critiquer"]


def test_custom_supervisor_starts_with_analyzer():
    state = {
        "work_type": "custom",
        "custom_pipeline": ["analyzer", "writer"],
    }
    result = custom_supervisor_next(state)
    assert result["next_step"] == "analyzer"


def test_custom_supervisor_moves_to_writer_after_analysis():
    state = {
        "work_type": "custom",
        "custom_pipeline": ["analyzer", "writer"],
        "requirements": "done",
    }
    result = custom_supervisor_next(state)
    assert result["next_step"] == "writer"


def test_custom_supervisor_skips_stuck_coder_gen_after_max_attempts():
    state = {
        "work_type": "custom",
        "custom_pipeline": ["analyzer", "coder_gen", "writer"],
        "requirements": "done",
        "coder_gen_attempts": 2,
        "code_generated": False,
    }
    result = custom_supervisor_next(state)
    assert result["next_step"] == "writer"


def test_custom_supervisor_skips_stuck_bibliography_after_max_attempts():
    state = {
        "work_type": "custom",
        "custom_pipeline": ["analyzer", "writer", "bibliography_verifier", "docx_builder"],
        "requirements": "done",
        "content_draft": '{"intro":["x"]}',
        "bibliography_verified": False,
        "bibliography_attempts": 2,
    }
    result = custom_supervisor_next(state)
    assert result["next_step"] == "docx_builder"


def test_custom_supervisor_revision_resets_bib_style_flags():
    state = {
        "work_type": "custom",
        "custom_pipeline": ["analyzer", "writer", "bibliography_verifier", "style_polisher", "critiquer"],
        "requirements": "done",
        "content_draft": '{"intro":["x"]}',
        "bibliography_verified": True,
        "style_polished": True,
        "critique_notes": "Нужно расширить введение",
        "critique_rerun": "writer",
        "revision_number": 0,
        "max_revisions": 3,
    }
    result = custom_supervisor_next(state)
    assert result["next_step"] == "writer"
    assert result["bibliography_verified"] is False
    assert result["style_polished"] is False
