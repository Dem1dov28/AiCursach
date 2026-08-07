"""API tests for job pause and delete."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.server import app


def test_pause_running_job() -> None:
    client = TestClient(app)
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {"id": "job-1", "status": "running"}
        with patch("backend.api.routes.jobs.submit_pause", return_value=True) as mock_pause:
            response = client.post("/api/jobs/job-1/pause")

    assert response.status_code == 200
    assert response.json()["status"] == "pausing"
    mock_pause.assert_called_once_with("job-1")


def test_pause_already_paused_returns_ok() -> None:
    client = TestClient(app)
    with patch("backend.api.routes.jobs._get_job") as mock_get:
        mock_get.execute.return_value = {"id": "job-1", "status": "paused"}
        with patch("backend.api.routes.jobs.submit_pause") as mock_pause:
            response = client.post("/api/jobs/job-1/pause")

    assert response.status_code == 200
    assert response.json()["status"] == "paused"
    mock_pause.assert_not_called()


def test_delete_completed_job() -> None:
    client = TestClient(app)
    with patch("backend.api.routes.jobs._delete_job") as mock_delete:
        response = client.delete("/api/jobs/job-1")

    assert response.status_code == 200
    mock_delete.execute.assert_called_once_with("job-1")


def test_delete_running_job_rejected() -> None:
    client = TestClient(app)
    with patch("backend.api.routes.jobs._delete_job") as mock_delete:
        mock_delete.execute.side_effect = ValueError("Нельзя удалить выполняющуюся задачу")
        response = client.delete("/api/jobs/job-1")

    assert response.status_code == 400
