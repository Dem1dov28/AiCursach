"""Use case: SSE event stream for a running job."""

from __future__ import annotations

import asyncio
import json
import queue
from collections.abc import AsyncIterator

from backend.application.jobs.get_job import GetJob
from backend.application.container import event_publisher


def sse_payload(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class StreamJobEvents:
    def __init__(self) -> None:
        self._get_job = GetJob()

    async def events(self, job_id: str) -> AsyncIterator[str]:
        snapshot = self._get_job.execute(job_id)
        if not snapshot:
            return

        yield sse_payload({"type": "snapshot", "job": snapshot})

        patch = snapshot.get("state_patch") or {}
        if patch:
            yield sse_payload({"type": "state_patch", "patch": patch})
            if patch.get("awaiting_clarification") and patch.get("pending_clarification"):
                yield sse_payload(
                    {
                        "type": "breakpoint",
                        "reason": "clarification",
                        "patch": patch,
                        "clarification": patch.get("pending_clarification"),
                    }
                )
            elif patch.get("awaiting_plan_approval"):
                yield sse_payload(
                    {
                        "type": "breakpoint",
                        "reason": "plan_approval",
                        "patch": patch,
                    }
                )
            elif patch.get("awaiting_team_approval") and patch.get("pending_team"):
                yield sse_payload(
                    {
                        "type": "breakpoint",
                        "reason": "team_approval",
                        "patch": patch,
                        "team": patch.get("pending_team"),
                    }
                )

        if snapshot["status"] in ("completed", "failed"):
            yield sse_payload({"type": "done", "status": snapshot["status"], "job": snapshot})
            return

        sub = event_publisher().subscribe(job_id)

        def _get_event() -> dict | None:
            try:
                return sub.get(timeout=25)
            except queue.Empty:
                return {"type": "heartbeat"}

        try:
            while True:
                event = await asyncio.to_thread(_get_event)
                if event is None:
                    current = self._get_job.execute(job_id)
                    if current:
                        yield sse_payload(
                            {"type": "done", "status": current["status"], "job": current}
                        )
                    break

                if event.get("type") == "heartbeat":
                    yield ": heartbeat\n\n"
                    current = self._get_job.execute(job_id)
                    if current and current["status"] in ("completed", "failed"):
                        yield sse_payload(
                            {"type": "done", "status": current["status"], "job": current}
                        )
                        break
                    continue

                yield sse_payload(event)
                if event.get("type") == "done":
                    break
        finally:
            event_publisher().unsubscribe(job_id, sub)
