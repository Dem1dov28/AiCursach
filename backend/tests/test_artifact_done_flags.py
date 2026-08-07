"""Honest done-flags for diagrammer / assets (P2 stage 1)."""

from __future__ import annotations

from unittest.mock import patch

from backend.domain.workflow.custom_pipeline import MAX_ARTIFACT_ATTEMPTS, custom_supervisor_next
from backend.infrastructure.adapters.diagram_gen import diagrams_render_success, png_paths
from backend.infrastructure.langgraph.nodes.assets_builder import assets_builder_node
from backend.infrastructure.langgraph.nodes.diagrammer import diagrammer_node


def test_png_paths_filters_puml():
    files = [
        "projects/X/Материалы/Диаграммы/puml/a.puml",
        "projects/X/Материалы/Диаграммы/png/a.png",
    ]
    assert png_paths(files) == [files[1]]


def test_diagrams_render_success_requires_png_not_puml_only():
    package = {"plantuml": [{"filename": "a.puml", "content": "@startuml\nA\n@enduml"}]}
    puml_only = ["projects/X/a.puml"]
    assert not diagrams_render_success(package, all_files=puml_only, render_ok=False)
    assert not diagrams_render_success(package, all_files=puml_only, render_ok=True)

    with_png = puml_only + ["projects/X/a.png"]
    assert diagrams_render_success(package, all_files=with_png, render_ok=True)
    assert not diagrams_render_success(package, all_files=with_png, render_ok=False)


def test_diagrams_idef0_success_on_png():
    package = {"idef0": {"boxes": []}}
    assert diagrams_render_success(
        package,
        all_files=["projects/X/idef0_a0.png"],
        render_ok=True,
    )


def test_diagrammer_node_does_not_mark_done_without_png():
    with (
        patch("backend.infrastructure.langgraph.nodes.diagrammer.get_llm"),
        patch(
            "backend.infrastructure.langgraph.nodes.diagrammer.llm_text",
            return_value='{"plantuml":[{"filename":"x.puml","content":"A -> B"}]}',
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.diagrammer.apply_diagram_package",
            return_value=(["projects/X/x.puml"], ["saved puml"], False, "render failed"),
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.diagrammer.gate_after_llm",
            return_value={},
        ),
    ):
        result = diagrammer_node(
            {
                "project_name": "X",
                "topic": "t",
                "requirements": "r",
                "diagram_types": "usecase",
            }
        )
    assert result["diagrams_generated"] is False
    assert result["diagrammer_attempts"] == 1


def test_assets_builder_skipped_when_not_needed():
    result = assets_builder_node(
        {
            "work_type": "lab",
            "detected_work_kind": "lab",
            "needs_charts": False,
            "needs_excel": False,
            "project_name": "LabX",
        }
    )
    assert result["coursework_assets_done"] is True
    assert result["assets_quality"] == "skipped"


def test_assets_builder_fails_without_topic_package():
    with (
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder.prepare_coursework_assets",
            return_value=([], ["no iouz"], "none"),
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder._llm_asset_package",
            return_value=(None, {}, ["bad package"]),
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder.gate_after_llm",
            return_value={},
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder.uses_coursework_docx",
            return_value=True,
        ),
    ):
        result = assets_builder_node(
            {
                "work_type": "coursework",
                "needs_charts": True,
                "needs_excel": True,
                "project_name": "CW",
                "topic": "ИС",
            }
        )
    assert result["coursework_assets_done"] is False
    assert result["assets_quality"] == "failed"
    assert result["assets_builder_attempts"] >= 1


def test_assets_builder_iouz_marks_done():
    with patch(
        "backend.infrastructure.langgraph.nodes.assets_builder.prepare_coursework_assets",
        return_value=(["projects/X/a.xlsx"], ["iouz ok"], "iouz"),
    ), patch(
        "backend.infrastructure.langgraph.nodes.assets_builder.gate_after_llm",
        return_value={},
    ), patch(
        "backend.infrastructure.langgraph.nodes.assets_builder.uses_coursework_docx",
        return_value=True,
    ):
        result = assets_builder_node(
            {
                "work_type": "coursework",
                "needs_charts": True,
                "project_name": "CW",
                "topic": "ИОУЗ склад",
            }
        )
    assert result["coursework_assets_done"] is True
    assert result["assets_quality"] == "iouz"


def test_pipeline_advances_after_placeholder_attempts():
    state = {
        "work_type": "custom",
        "custom_pipeline": ["analyzer", "assets_builder", "writer"],
        "requirements": "done",
        "coursework_assets_done": False,
        "assets_builder_attempts": MAX_ARTIFACT_ATTEMPTS,
        "assets_quality": "placeholder",
    }
    result = custom_supervisor_next(state)
    assert result["next_step"] == "writer"
