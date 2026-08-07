"""Tests for work profile helpers (coursework writer / docx routing)."""

from backend.domain.workflow.work_profile import uses_coursework_docx, writer_uses_coursework_prompt


def test_uses_coursework_docx_for_auto_detected_coursework():
    assert uses_coursework_docx(
        {"work_type": "auto", "detected_work_kind": "coursework"}
    )


def test_uses_coursework_docx_false_for_plain_lab():
    assert not uses_coursework_docx({"work_type": "lab", "detected_work_kind": "lab"})


def test_writer_coursework_prompt_for_auto_coursework():
    assert writer_uses_coursework_prompt(
        {"work_type": "auto", "detected_work_kind": "coursework"}
    )
