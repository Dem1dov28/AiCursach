"""HTTP adapter for graph topology (thin controller)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.application.graph.get_topology import GetAgentCatalog, GetGraphTopology

router = APIRouter(prefix="/api/graph", tags=["graph"])
_get_topology = GetGraphTopology()
_get_catalog = GetAgentCatalog()


@router.get("/topology")
async def graph_topology(
    work_type: str = Query("full"),
    pipeline: str | None = Query(default=None, description="JSON array or comma-separated node ids"),
):
    custom_pipeline = _get_topology.parse_pipeline_param(pipeline)
    topology = _get_topology.execute(work_type, custom_pipeline=custom_pipeline)
    return topology.to_dict()


@router.get("/catalog")
async def graph_catalog():
    return {"agents": _get_catalog.execute()}
