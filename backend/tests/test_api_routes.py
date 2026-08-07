"""API integration tests (HTTP layer)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_config
from backend.api.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_status(client: TestClient) -> None:
    get_config.cache_clear()
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}, clear=False):
        get_config.cache_clear()
        with patch("backend.api.deps.job_repository") as mock_repo:
            mock_repo.return_value.ping.return_value = True
            response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["llm_configured"] is True
    assert body["database_ok"] is True
    assert body["ok"] is True


def test_health_reports_db_failure(client: TestClient) -> None:
    get_config.cache_clear()
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}, clear=False):
        get_config.cache_clear()
        with patch("backend.api.deps.job_repository") as mock_repo:
            mock_repo.return_value.ping.side_effect = RuntimeError("connection refused")
            response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["database_ok"] is False
    assert body["ok"] is False
    assert "connection refused" in (body.get("database_error") or "")


def test_graph_topology_auto(client: TestClient) -> None:
    response = client.get("/api/graph/topology", params={"work_type": "auto"})

    assert response.status_code == 200
    body = response.json()
    assert body["work_type"] == "auto"
    node_ids = {node["id"] for node in body["nodes"]}
    assert "supervisor" in node_ids
    assert "writer" in node_ids
    assert "analyzer" in node_ids


def test_graph_topology_custom_pipeline(client: TestClient) -> None:
    pipeline = '["analyzer", "writer", "docx_builder"]'
    response = client.get(
        "/api/graph/topology",
        params={"work_type": "custom", "pipeline": pipeline},
    )

    assert response.status_code == 200
    body = response.json()
    worker_ids = [node["id"] for node in body["nodes"] if node["id"] != "supervisor"]
    assert worker_ids == ["analyzer", "writer", "docx_builder"]


def test_jobs_list_empty(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._list_jobs") as mock_list:
        mock_list.execute.return_value = []
        response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json()["jobs"] == []


def test_job_not_found(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = None
        response = client.get("/api/jobs/missing-id")

    assert response.status_code == 404


def test_resume_paused_job(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {"id": "job-1", "status": "paused"}
        with patch("backend.api.routes.jobs.submit_resume", return_value=True) as mock_resume:
            response = client.post(
                "/api/jobs/job-1/resume",
                json={"structure_outline": "1. Введение\n2. Основная часть"},
            )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    mock_resume.assert_called_once_with("job-1", structure_outline="1. Введение\n2. Основная часть")


def test_resume_conflict_when_not_ready(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {"id": "job-1", "status": "paused"}
        with patch("backend.api.routes.jobs.submit_resume", return_value=False):
            response = client.post("/api/jobs/job-1/resume", json={"structure_outline": ""})

    assert response.status_code == 409


def test_clarification_answer(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {"id": "job-1", "status": "paused"}
        with patch("backend.api.routes.jobs.submit_clarification", return_value=True) as mock_clar:
            response = client.post(
                "/api/jobs/job-1/clarification",
                json={"selected_option": "Вариант А", "custom_text": ""},
            )

    assert response.status_code == 200
    mock_clar.assert_called_once_with(
        "job-1",
        selected_option="Вариант А",
        custom_text="",
    )


def test_clarification_requires_answer(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {"id": "job-1", "status": "paused"}
        response = client.post(
            "/api/jobs/job-1/clarification",
            json={"selected_option": "", "custom_text": ""},
        )

    assert response.status_code == 400


def test_team_approval(client: TestClient) -> None:
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {
            "id": "job-1",
            "status": "paused",
            "state_patch": {"awaiting_team_approval": True},
        }
        with patch("backend.api.routes.jobs.submit_team_approval", return_value=True) as mock_team:
            response = client.post(
                "/api/jobs/job-1/team",
                json={"custom_pipeline": ["analyzer", "writer", "docx_builder"]},
            )

    assert response.status_code == 200
    mock_team.assert_called_once_with(
        "job-1",
        custom_pipeline=["analyzer", "writer", "docx_builder"],
    )
