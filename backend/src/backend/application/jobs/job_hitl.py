"""Human-in-the-Loop coordination: waiters, payloads, submit handlers."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from backend.application.container import job_repository

EmitFn = Callable[[str, dict[str, Any]], None]


class HitlCoordinator:
    """In-memory HITL state for pausing/resuming jobs within active threads."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._waiters: dict[str, threading.Event] = {}
        self._payloads: dict[str, dict[str, Any]] = {}
        self._pending_clarification: dict[str, dict[str, str]] = {}
        self._active_threads: dict[str, str] = {}
        self._stream_stop: set[str] = set()

    def is_thread_active(self, job_id: str) -> bool:
        return job_id in self._active_threads

    def set_thread_mode(self, job_id: str, mode: str) -> None:
        self._active_threads[job_id] = mode

    def clear_thread(self, job_id: str) -> None:
        self._active_threads.pop(job_id, None)

    def cleanup_job(self, job_id: str) -> None:
        with self._lock:
            self._waiters.pop(job_id, None)
            self._payloads.pop(job_id, None)
            self._pending_clarification.pop(job_id, None)
            self._stream_stop.discard(job_id)
        self.clear_thread(job_id)

    def signal_stream_stop(self, job_id: str) -> None:
        with self._lock:
            self._stream_stop.add(job_id)

    def consume_stream_stop(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._stream_stop:
                self._stream_stop.discard(job_id)
                return True
        return False

    def prepare_pause(self, job_id: str, final_state: dict[str, Any], emit: EmitFn) -> None:
        """Persist paused state and register waiter before SSE breakpoint reaches UI."""
        job_repository().update_job(job_id, status="paused", final_state=final_state)
        with self._lock:
            event = self._waiters.get(job_id)
            if event is None:
                event = threading.Event()
                self._waiters[job_id] = event
            pending = self._pending_clarification.pop(job_id, None)
            if pending:
                self._payloads[job_id] = {"clarification_answer": pending}
                event.set()
        emit(job_id, {"type": "status", "status": "paused"})

    def wait_for_resume(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            if job_id in self._payloads:
                payload = dict(self._payloads.pop(job_id))
                self._waiters.pop(job_id, None)
                return payload
            event = self._waiters.get(job_id)
            if event is None:
                event = threading.Event()
                self._waiters[job_id] = event
            elif event.is_set():
                payload = dict(self._payloads.pop(job_id, {}))
                self._waiters.pop(job_id, None)
                return payload

        event.wait()

        with self._lock:
            payload = dict(self._payloads.pop(job_id, {}))
            self._waiters.pop(job_id, None)
        return payload

    def try_signal(self, job_id: str, payload: dict[str, Any]) -> bool:
        """Deliver payload to a waiting thread. Returns True if waiter existed."""
        with self._lock:
            if job_id not in self._waiters:
                return False
            self._payloads[job_id] = payload
            self._waiters[job_id].set()
            return True

    def store_pending_clarification(self, job_id: str, answer: dict[str, str]) -> None:
        with self._lock:
            self._pending_clarification[job_id] = answer


hitl = HitlCoordinator()

_spawn_lock = threading.Lock()
_spawning_jobs: set[str] = set()


def is_job_thread_active(job_id: str) -> bool:
    return hitl.is_thread_active(job_id)


def submit_clarification(job_id: str, *, selected_option: str = "", custom_text: str = "") -> bool:
    answer = {
        "selected_option": selected_option.strip(),
        "custom_text": custom_text.strip(),
    }
    if not answer["selected_option"] and not answer["custom_text"]:
        return False

    if hitl.try_signal(job_id, {"clarification_answer": answer}):
        return True
    if hitl.is_thread_active(job_id):
        hitl.store_pending_clarification(job_id, answer)
        return True

    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return False
    fs = record.final_state or {}
    awaiting = bool(fs.get("awaiting_clarification"))
    if record.status not in ("paused", "running") or (record.status == "running" and not awaiting):
        return False
    if hitl.is_thread_active(job_id):
        hitl.store_pending_clarification(job_id, answer)
        return True

    from backend.application.jobs.job_runner import spawn_continue_thread

    spawn_continue_thread(job_id=job_id, clarification_answer=answer)
    return True


def submit_team_approval(job_id: str, *, custom_pipeline: list[str] | None = None) -> bool:
    answer: dict[str, Any] = {"approved": True}
    if custom_pipeline:
        answer["custom_pipeline"] = custom_pipeline

    if hitl.try_signal(job_id, {"team_approval_answer": answer}):
        return True

    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return False
    fs = record.final_state or {}
    if record.status not in ("paused", "running") or not fs.get("awaiting_team_approval"):
        return False
    if hitl.is_thread_active(job_id):
        return hitl.try_signal(job_id, {"team_approval_answer": answer})

    with _spawn_lock:
        if job_id in _spawning_jobs or hitl.is_thread_active(job_id):
            return hitl.try_signal(job_id, {"team_approval_answer": answer})
        _spawning_jobs.add(job_id)

    from backend.application.jobs.job_runner import run_continue_thread

    def _run() -> None:
        try:
            run_continue_thread(job_id=job_id, team_approval_answer=answer)
        finally:
            with _spawn_lock:
                _spawning_jobs.discard(job_id)

    threading.Thread(target=_run, daemon=True).start()
    return True


def submit_pause(job_id: str) -> bool:
    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return False
    if record.status == "paused":
        return True
    if record.status != "running":
        return False

    fs = dict(record.final_state or {})
    fs["user_pause_requested"] = True
    store.update_job(job_id, final_state=fs)
    hitl.signal_stream_stop(job_id)
    if hitl.try_signal(job_id, {"user_pause": True}):
        return True
    return True


def submit_resume(job_id: str, *, structure_outline: str = "") -> bool:
    payload = {"structure_outline": structure_outline.strip()}
    if hitl.try_signal(job_id, payload):
        return True

    store = job_repository()
    record = store.get_job(job_id)
    if not record or record.status != "paused":
        return False
    if hitl.is_thread_active(job_id):
        return False

    from backend.application.jobs.job_runner import spawn_continue_thread

    spawn_continue_thread(job_id=job_id, structure_outline=payload["structure_outline"])
    return True


def submit_rerun(
    job_id: str,
    *,
    from_node: str,
    structure_outline: str = "",
    prompt_override: str = "",
) -> bool:
    from backend.domain.workflow.rerun import normalize_rerun_target

    store = job_repository()
    record = store.get_job(job_id)
    if not record:
        return False
    if record.status in ("running", "queued"):
        return False

    node = normalize_rerun_target(from_node)
    payload = {
        "rerun_from": node,
        "structure_outline": structure_outline.strip(),
        "prompt_override": prompt_override.strip(),
    }

    if hitl.try_signal(job_id, payload):
        return True

    if record.status in ("completed", "failed", "paused"):
        if hitl.is_thread_active(job_id):
            return False
        from backend.application.jobs.job_runner import spawn_rerun_thread

        hitl.set_thread_mode(job_id, "rerun")
        spawn_rerun_thread(
            job_id=job_id,
            from_node=node,
            structure_outline=structure_outline,
            prompt_override=prompt_override,
        )
        return True
    return False
