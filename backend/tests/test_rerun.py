"""Tests for manual rerun domain rules."""

from backend.domain.workflow.rerun import (
    build_rerun_patches,
    normalize_revision_target,
    normalize_rerun_target,
)


def test_normalize_aliases():
    assert normalize_rerun_target("reviewer") == "critiquer"
    assert normalize_rerun_target("planner") == "analyzer"


def test_normalize_revision_target():
    assert normalize_revision_target("coder") == "coder_gen"
    assert normalize_revision_target("none") == "writer"
    assert normalize_revision_target("researcher") == "writer"


def test_build_rerun_patches_clears_docx_for_writer():
    patches = build_rerun_patches("writer")
    assert patches["force_rerun"] == "writer"
    assert patches["output_docx_path"] == ""
