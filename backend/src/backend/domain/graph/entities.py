"""Domain entities for workflow graph visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

NodeKind = Literal["supervisor", "worker"]
EdgeKind = Literal["flow", "loop", "route"]


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    role: str
    kind: NodeKind
    position: dict[str, float]


@dataclass(frozen=True)
class GraphEdge:
    id: str
    source: str
    target: str
    kind: EdgeKind
    label: str = ""


@dataclass(frozen=True)
class GraphTopology:
    work_type: str
    nodes: tuple[GraphNode, ...] = field(default_factory=tuple)
    edges: tuple[GraphEdge, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "work_type": self.work_type,
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "role": n.role,
                    "kind": n.kind,
                    "position": n.position,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "kind": e.kind,
                    "label": e.label,
                }
                for e in self.edges
            ],
        }
