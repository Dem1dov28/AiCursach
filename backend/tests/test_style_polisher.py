"""Tests for style polisher node (no LLM)."""

from backend.infrastructure.langgraph.nodes.style_polisher import style_polisher_node


def test_style_polisher_skips_empty_draft():
    result = style_polisher_node({"content_draft": "", "work_type": "auto"})
    assert result["style_polished"] is True


def test_style_polisher_disabled_in_settings():
    result = style_polisher_node(
        {
            "content_draft": '{"sections": [{"body": "Важно отметить что..."}]}',
            "work_type": "auto",
            "enable_style_polisher": False,
        }
    )
    assert result["style_polished"] is True
    assert "отключена" in result["tool_log"][0].lower()
