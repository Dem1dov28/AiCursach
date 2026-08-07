"""Tests for domain graph topology."""

from backend.domain.graph.topology_builder import build_graph_topology


def test_coursework_topology_has_core_writing_loop():
    topology = build_graph_topology("coursework")
    node_ids = {node.id for node in topology.nodes}
    assert "writer" in node_ids
    assert "critiquer" in node_ids
    assert "project_init" not in node_ids
    flow_edges = [(edge.source, edge.target) for edge in topology.edges if edge.kind == "flow"]
    assert ("analyzer", "researcher") in flow_edges
    assert ("researcher", "writer") in flow_edges
    loop_edges = [edge for edge in topology.edges if edge.kind == "loop"]
    assert any(edge.source == "critiquer" and edge.target == "writer" for edge in loop_edges)


def test_lab_topology_includes_code_nodes():
    topology = build_graph_topology("lab")
    node_ids = {node.id for node in topology.nodes}
    assert "coder_gen" in node_ids
    assert "code_runner" in node_ids
    assert "project_init" in node_ids
    flow_edges = [(edge.source, edge.target) for edge in topology.edges if edge.kind == "flow"]
    assert ("analyzer", "project_init") in flow_edges
    assert ("project_init", "researcher") in flow_edges
    assert ("docx_builder", "critiquer") in flow_edges
