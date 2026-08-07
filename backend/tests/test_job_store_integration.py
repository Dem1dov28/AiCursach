"""Opt-in integration tests against live PostgreSQL."""

from __future__ import annotations

import uuid

import pytest

from backend.core.config import get_config
from backend.infrastructure.persistence.job_store import JobStore

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def live_store() -> JobStore:
    store = JobStore(url=get_config().database_url)
    try:
        if not store.ping():
            pytest.skip("PostgreSQL ping returned False")
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    store.init_schema()
    return store


def _delete_job(store: JobStore, job_id: str) -> None:
    with store._connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        conn.commit()


def test_create_get_and_step_roundtrip(live_store: JobStore) -> None:
    job_id = f"pytest-{uuid.uuid4().hex[:12]}"
    try:
        created = live_store.create_job(job_id, project_name="Integration", work_type="lab")
        assert created.id == job_id
        assert created.status == "queued"

        fetched = live_store.get_job(job_id)
        assert fetched is not None
        assert fetched.project_name == "Integration"

        live_store.add_step(job_id, step=1, agent="writer", message="draft ready")
        with_steps = live_store.get_job(job_id)
        assert with_steps is not None
        assert len(with_steps.steps) == 1
        assert with_steps.steps[0]["agent"] == "writer"
    finally:
        _delete_job(live_store, job_id)


def test_draft_snapshots_roundtrip(live_store: JobStore) -> None:
    job_id = f"pytest-{uuid.uuid4().hex[:12]}"
    try:
        live_store.create_job(job_id, project_name="Draft", work_type="lab")
        live_store.add_draft_snapshot(job_id, step=1, agent="writer", content_draft="Version A")
        live_store.add_draft_snapshot(job_id, step=2, agent="writer", content_draft="Version B")

        snapshots = live_store.get_draft_snapshots(job_id)
        assert len(snapshots) == 2
        assert snapshots[0]["content_draft"] == "Version A"
        assert snapshots[1]["content_draft"] == "Version B"
    finally:
        _delete_job(live_store, job_id)
