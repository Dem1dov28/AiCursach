"""Domain rules for manual workflow rerun."""

from __future__ import annotations

RERUN_TARGETS = frozenset({
    "writer",
    "researcher",
    "analyzer",
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
})

_ALIASES = {
    "coder": "coder_gen",
    "code": "coder_gen",
    "diagram": "diagrammer",
    "diagrams": "diagrammer",
    "builder": "docx_builder",
    "docx": "docx_builder",
    "assets": "assets_builder",
    "excel": "assets_builder",
    "annex": "annex_builder",
    "appendices": "annex_builder",
    "приложения": "annex_builder",
    "antiplag": "antiplagiat",
    "antiplagiat": "antiplagiat",
    "оригинальность": "antiplagiat",
    "reviewer": "critiquer",
    "planner": "analyzer",
    "bibliography": "bibliography_verifier",
    "bib": "bibliography_verifier",
    "style": "style_polisher",
    "polish": "style_polisher",
}


REVISION_TARGETS = frozenset({
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
})


def normalize_revision_target(target: str) -> str:
    """Map critique rerun hint to a valid revision node (subset of RERUN_TARGETS)."""
    key = (target or "").strip().lower()
    if key in ("none", ""):
        return "writer"
    key = _ALIASES.get(key, key)
    if key in REVISION_TARGETS:
        return key
    return "writer"


def normalize_rerun_target(target: str) -> str:
    key = (target or "").strip().lower()
    key = _ALIASES.get(key, key)
    if key in RERUN_TARGETS:
        return key
    return "writer"


def build_rerun_patches(target: str, *, set_force_flag: bool = True) -> dict:
    """State patches applied before restarting from a node."""
    node = normalize_rerun_target(target)
    patches: dict = {
        "critique_rerun": node,
        "critique_notes": f"Manual rerun → {node}",
    }
    if set_force_flag:
        patches["force_rerun"] = node
    if node in ("writer", "bibliography_verifier", "style_polisher", "docx_builder", "assets_builder", "annex_builder", "antiplagiat", "coder_gen", "code_runner", "diagrammer"):
        patches["output_docx_path"] = ""
    if node in ("writer", "bibliography_verifier", "style_polisher"):
        patches["bibliography_verified"] = False
        patches["style_polished"] = False
        patches["bibliography_attempts"] = 0
        patches["style_polisher_attempts"] = 0
    if node == "assets_builder":
        patches["coursework_assets_done"] = False
        patches["assets_builder_attempts"] = 0
        patches["assets_quality"] = ""
    if node == "annex_builder":
        patches["annex_plan_done"] = False
        patches["annex_builder_attempts"] = 0
        patches["annex_plan"] = ""
    if node == "antiplagiat":
        patches["antiplagiat_done"] = False
        patches["antiplagiat_attempts"] = 0
        patches["antiplagiat_screenshot"] = ""
        patches["annex_reserved_letters"] = []
    if node == "coder_gen":
        patches["code_generated"] = False
        patches["code_run_done"] = False
        patches["coder_gen_attempts"] = 0
    if node == "code_runner":
        patches["code_run_done"] = False
    if node == "diagrammer":
        patches["diagrams_generated"] = False
        patches["diagrammer_attempts"] = 0
    if node == "writer":
        patches["awaiting_plan_approval"] = False
    return patches
