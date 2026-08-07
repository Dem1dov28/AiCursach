"""Use case: expose workflow graph topology for the UI."""

from __future__ import annotations

import json

from backend.domain.graph.entities import GraphTopology
from backend.domain.graph.topology_builder import agent_catalog, build_graph_topology
from backend.domain.workflow.custom_pipeline import normalize_custom_pipeline


class GetGraphTopology:
    """Application service — no HTTP or LangGraph dependencies."""

    def execute(
        self,
        work_type: str = "full",
        custom_pipeline: list[str] | None = None,
    ) -> GraphTopology:
        return build_graph_topology(work_type, custom_pipeline=custom_pipeline)

    @staticmethod
    def parse_pipeline_param(raw: str | None) -> list[str] | None:
        if not raw or not raw.strip():
            return None
        text = raw.strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return normalize_custom_pipeline(parsed)
            except json.JSONDecodeError:
                pass
        return normalize_custom_pipeline([part.strip() for part in text.split(",") if part.strip()])


class GetAgentCatalog:
    def execute(self) -> list[dict[str, str]]:
        return agent_catalog()
