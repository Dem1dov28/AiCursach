"""JobStore unit tests (mocked PostgreSQL)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.core.config import AppConfig, get_config
from backend.domain.jobs.records import JobRecord
from backend.infrastructure.persistence.job_store import JobStore, database_url


class _FakeCursor:
    def __init__(self, *, fetchone=None, fetchall=None, rowcount: int = 0) -> None:
        self.executed: list[tuple[str, tuple | None]] = []
        self._fetchone = fetchone
        self._fetchall = fetchall or []
        self.rowcount = rowcount

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.executed.append((sql.strip(), params))
        if "DELETE FROM jobs" in sql:
            self.rowcount = 1 if params and params[0] != "missing" else 0

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None


class _FakeConn:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None


def _store_with_cursor(cursor: _FakeCursor) -> JobStore:
    store = JobStore(url="postgresql://test/db")
    conn = _FakeConn(cursor)

    @contextmanager
    def fake_connect():
        yield conn

    store._connect = fake_connect  # type: ignore[method-assign]
    return store


def test_database_url_rejects_empty():
    get_config.cache_clear()
    cfg = AppConfig(
        web_host="0.0.0.0",
        web_port=19407,
        graph_recursion_limit=80,
        max_revisions=3,
        data_dir=__import__("pathlib").Path("/tmp/data"),
        use_server_storage=True,
        database_url="",
        openrouter_api_key="",
        openai_api_key="",
        openrouter_model="m",
        openai_model="m",
        openrouter_base_url="",
        openrouter_site_url="",
        openrouter_app_name="",
        openai_base_url="",
        crossref_verify=True,
        tavily_api_key="",
        openalex_mailto="",
        semantic_scholar_api_key="",
        chrome_path="",
        chromium_flags="",
        llm_input_usd_per_token=None,
        llm_output_usd_per_token=None,
    )
    with patch("backend.infrastructure.persistence.job_store.get_config", return_value=cfg):
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            database_url()


def test_create_job_inserts_and_returns_record():
    cursor = _FakeCursor()
    store = _store_with_cursor(cursor)

    record = store.create_job("job-1", project_name="Demo", work_type="lab")

    assert record.id == "job-1"
    assert record.status == "queued"
    assert record.project_name == "Demo"
    assert record.work_type == "lab"
    assert len(cursor.executed) == 1
    sql, params = cursor.executed[0]
    assert "INSERT INTO jobs" in sql
    assert params[0] == "job-1"
    assert params[4] == "lab"


def test_get_job_returns_none_when_missing():
    cursor = _FakeCursor(fetchone=None)
    store = _store_with_cursor(cursor)

    assert store.get_job("missing") is None


def test_get_job_maps_row_and_steps():
    created = datetime(2024, 1, 2, tzinfo=timezone.utc)
    cursor = _FakeCursor(
        fetchone=(
            "job-1",
            "running",
            created,
            "Project",
            "coursework",
            {"topic": "AI"},
            "",
            "out.zip",
            True,
        ),
        fetchall=[(1, "writer", "done", "")],
    )
    store = _store_with_cursor(cursor)

    record = store.get_job("job-1")

    assert record is not None
    assert record.id == "job-1"
    assert record.status == "running"
    assert record.project_name == "Project"
    assert record.final_state == {"topic": "AI"}
    assert record.has_zip is True
    assert record.steps == [{"step": 1, "agent": "writer", "message": "done", "detail": ""}]


def test_add_draft_snapshot_skips_blank_content():
    store = JobStore(url="postgresql://test/db")
    connect = MagicMock()
    store._connect = connect  # type: ignore[method-assign]

    store.add_draft_snapshot("job-1", step=1, agent="writer", content_draft="   ")

    connect.assert_not_called()


def test_add_draft_snapshot_inserts_when_content_present():
    cursor = _FakeCursor()
    store = _store_with_cursor(cursor)

    store.add_draft_snapshot("job-1", step=2, agent="writer", content_draft="Hello")

    assert len(cursor.executed) == 1
    sql, params = cursor.executed[0]
    assert "job_draft_snapshots" in sql
    assert params == ("job-1", 2, "writer", "Hello")


def test_ping_executes_select_one():
    cursor = _FakeCursor(fetchone=(1,))
    store = _store_with_cursor(cursor)

    assert store.ping() is True
    assert "SELECT 1" in cursor.executed[0][0]


def test_job_record_to_dict_includes_topic():
    record = JobRecord(id="j1", final_state={"topic": "Test topic", "output_docx_path": "/out.docx"})
    data = record.to_dict()
    assert data["topic"] == "Test topic"
    assert data["output_docx"] == "/out.docx"
    assert data["storage"] == "postgresql"


def test_delete_job_removes_row():
    cursor = _FakeCursor()
    store = _store_with_cursor(cursor)

    assert store.delete_job("job-1") is True
    assert len(cursor.executed) == 1
    assert "DELETE FROM jobs" in cursor.executed[0][0]
    assert cursor.executed[0][1] == ("job-1",)

    cursor2 = _FakeCursor()
    store2 = _store_with_cursor(cursor2)
    assert store2.delete_job("missing") is False
