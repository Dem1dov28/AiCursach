"""Unit tests for HITL coordinator."""

from __future__ import annotations

import threading
import time

from backend.application.jobs.job_hitl import HitlCoordinator


def test_try_signal_delivers_payload_to_waiter():
    coordinator = HitlCoordinator()
    received: list[dict] = []

    def waiter():
        payload = coordinator.wait_for_resume("job-1")
        received.append(payload)

    thread = threading.Thread(target=waiter, daemon=True)
    thread.start()
    time.sleep(0.05)

    assert coordinator.try_signal("job-1", {"structure_outline": "1. Intro"})
    thread.join(timeout=2)

    assert received == [{"structure_outline": "1. Intro"}]


def test_try_signal_returns_false_without_waiter():
    coordinator = HitlCoordinator()
    assert not coordinator.try_signal("job-x", {"structure_outline": "x"})


def test_pending_clarification_applied_on_prepare_pause():
    coordinator = HitlCoordinator()
    emitted: list[tuple[str, dict]] = []
    coordinator.store_pending_clarification(
        "job-2",
        {"selected_option": "A", "custom_text": ""},
    )

    coordinator.prepare_pause("job-2", {"awaiting_clarification": True}, lambda jid, ev: emitted.append((jid, ev)))

    with coordinator._lock:
        assert coordinator._payloads["job-2"] == {
            "clarification_answer": {"selected_option": "A", "custom_text": ""},
        }
        assert coordinator._waiters["job-2"].is_set()
    assert emitted == [("job-2", {"type": "status", "status": "paused"})]


def test_cleanup_job_clears_state():
    coordinator = HitlCoordinator()
    coordinator.set_thread_mode("job-3", "run")
    with coordinator._lock:
        coordinator._waiters["job-3"] = threading.Event()
        coordinator._payloads["job-3"] = {"x": 1}

    coordinator.cleanup_job("job-3")

    assert not coordinator.is_thread_active("job-3")
    with coordinator._lock:
        assert "job-3" not in coordinator._waiters
        assert "job-3" not in coordinator._payloads
