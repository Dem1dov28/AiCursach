"""Tests for job store singleton lifecycle."""

from backend.infrastructure.persistence.job_store import get_job_store, reset_job_store


def test_get_job_store_does_not_init_schema(monkeypatch):
    reset_job_store()
    called = {"init": False}

    def fake_init_schema(self):
        called["init"] = True

    monkeypatch.setattr(
        "backend.infrastructure.persistence.job_store.JobStore.init_schema",
        fake_init_schema,
    )

    store = get_job_store()
    assert store is not None
    assert called["init"] is False

    reset_job_store()
