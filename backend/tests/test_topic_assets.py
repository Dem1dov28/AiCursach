"""Topic-driven coursework assets (P2 stage 3)."""

from __future__ import annotations

import sys
import types
from unittest.mock import patch

from backend.domain.document.asset_package import (
    asset_package_issues,
    normalize_asset_package,
)
from backend.infrastructure.langgraph.nodes.assets_builder import assets_builder_node


def test_normalize_asset_package_keeps_valid_charts():
    raw = {
        "table": {
            "columns": ["a", "b"],
            "rows": [{"a": "x", "b": "1"}, {"a": "y", "b": "2"}],
        },
        "charts": [
            {
                "type": "bar",
                "filename": "fig_a.png",
                "labels": ["A", "B", "C"],
                "values": [1, 2, 3],
                "ylabel": "N",
            },
            {"type": "pie", "labels": ["only"], "values": [1]},  # too few points
            {
                "type": "line",
                "filename": "bad name.png",
                "labels": ["1", "2"],
                "values": [5, 6],
            },
        ],
    }
    data = normalize_asset_package(raw)
    assert data["table"] is not None
    assert len(data["charts"]) == 2
    assert data["charts"][0]["filename"] == "fig_a.png"
    assert data["charts"][1]["filename"].endswith(".png")
    assert not asset_package_issues(data)


def test_asset_package_issues_without_charts():
    assert asset_package_issues({"charts": []})


def test_assets_builder_topic_success():
    package = {
        "table": {"columns": ["k", "v"], "rows": [{"k": "a", "v": "1"}]},
        "charts": [
            {
                "type": "bar",
                "filename": "fig_cmp.png",
                "labels": ["A", "B"],
                "values": [10, 20],
                "ylabel": "шт.",
            }
        ],
    }
    with (
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder.uses_coursework_docx",
            return_value=True,
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder.prepare_coursework_assets",
            side_effect=[
                ([], ["no iouz"], "none"),
                (["projects/X/fig_cmp.png", "projects/X/source.tsv"], ["ok"], "topic"),
            ],
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder._llm_asset_package",
            return_value=(package, package, ["llm ok"]),
        ),
        patch(
            "backend.infrastructure.langgraph.nodes.assets_builder.gate_after_llm",
            return_value={},
        ),
    ):
        result = assets_builder_node(
            {
                "work_type": "coursework",
                "needs_charts": True,
                "project_name": "CW",
                "topic": "ИС склада",
                "requirements": "графики по этапам",
            }
        )
    assert result["coursework_assets_done"] is True
    assert result["assets_quality"] == "topic"
    assert any(str(f).endswith(".png") for f in result["diagram_files"])


def test_render_topic_assets_writes_png(tmp_path, monkeypatch):
    from backend.infrastructure.adapters import coursework_bridge as bridge

    monkeypatch.setattr(bridge, "project_dir", lambda _name: tmp_path)
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    monkeypatch.setattr(
        bridge,
        "write_sample_data_tsv",
        lambda _name, rows: "Материалы/Данные/source.tsv",
    )

    created: list[str] = []

    def _write_png(filename: str):
        out = tmp_path / "Материалы" / "Графики" / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 80)
        created.append(filename)
        return out

    fake = types.ModuleType("tools.coursework.generate_charts")
    fake.bar_chart = lambda labels, values, ylabel, filename, **kw: _write_png(filename)
    fake.line_chart = lambda labels, values, ylabel, filename, **kw: _write_png(filename)
    fake.pie_chart = lambda labels, values, filename: _write_png(filename)
    fake.OUT = tmp_path

    tools_mod = types.ModuleType("tools")
    cw_mod = types.ModuleType("tools.coursework")
    with patch.dict(
        sys.modules,
        {
            "tools": tools_mod,
            "tools.coursework": cw_mod,
            "tools.coursework.generate_charts": fake,
        },
    ):
        artifacts, logs = bridge.render_topic_assets(
            "P",
            {
                "table": {"rows": [{"a": "1", "b": "2"}]},
                "charts": [
                    {
                        "type": "bar",
                        "filename": "fig_t.png",
                        "labels": ["A", "B"],
                        "values": [1, 2],
                        "ylabel": "N",
                    }
                ],
            },
        )

    assert "Материалы/Данные/source.tsv" in artifacts
    assert any(str(a).endswith("fig_t.png") for a in artifacts)
    assert created == ["fig_t.png"]
    assert any("График bar" in line for line in logs)
