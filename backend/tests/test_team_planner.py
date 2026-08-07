"""Tests for automatic team assembly from analyzer output."""

from backend.domain.workflow.team_planner import assemble_team_from_analysis


def test_assemble_lab_team_includes_code_nodes():
    pipeline, rationale, breakdown = assemble_team_from_analysis(
        {
            "topic": "Лабораторная 5",
            "needs_code": True,
            "needs_project_init": True,
            "needs_diagrams": True,
            "needs_research": True,
            "needs_excel": False,
        },
        work_type="auto",
    )
    assert pipeline[0] == "analyzer"
    assert "project_init" in pipeline
    assert "coder_gen" in pipeline
    assert "code_runner" in pipeline
    assert "writer" in pipeline
    assert "critiquer" in pipeline
    assert rationale
    assert len(breakdown) >= 4


def test_assemble_coursework_skips_project_init():
    pipeline, _, _ = assemble_team_from_analysis(
        {
            "topic": "Курсовая",
            "needs_code": False,
            "needs_project_init": False,
            "needs_diagrams": True,
            "needs_research": True,
        },
        work_type="auto",
    )
    assert "project_init" not in pipeline
    assert "diagrammer" in pipeline


def test_economics_coursework_excludes_code_agents():
    pipeline, rationale, _ = assemble_team_from_analysis(
        {
            "topic": "Экономика предприятия",
            "detected_work_kind": "coursework",
            "discipline": "economics",
            "needs_code": False,
            "needs_project_init": False,
            "needs_diagrams": False,
            "needs_excel": True,
            "needs_charts": True,
            "needs_research": True,
            "task_breakdown": [
                {"task": "Теория", "agent": "researcher"},
                {"task": "Текст", "agent": "writer"},
                {"task": "Таблицы", "agent": "assets_builder"},
                {"task": "Docx", "agent": "docx_builder"},
                {"task": "Review", "agent": "critiquer"},
            ],
        },
        work_type="auto",
    )
    assert "coder_gen" not in pipeline
    assert "code_runner" not in pipeline
    assert "project_init" not in pipeline
    assert "assets_builder" in pipeline
    assert "bibliography_verifier" in pipeline
    assert "style_polisher" in pipeline
    assert "economics" in rationale


def test_lab_team_includes_style_polisher():
    pipeline, _, _ = assemble_team_from_analysis(
        {
            "topic": "Лаб 3",
            "needs_code": True,
            "needs_project_init": True,
            "needs_research": False,
            "needs_diagrams": True,
        },
        work_type="auto",
    )
    assert "style_polisher" in pipeline
    assert "bibliography_verifier" not in pipeline
