"""Thread-safe pub/sub for job SSE streams."""

from __future__ import annotations

import queue
import threading
from collections import defaultdict
from typing import Any

Event = dict[str, Any]


class JobEventBus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[queue.Queue[Event | None]]] = defaultdict(list)

    def publish(self, job_id: str, event: Event) -> None:
        with self._lock:
            subs = list(self._subscribers.get(job_id, []))
        for sub in subs:
            try:
                sub.put_nowait(event)
            except queue.Full:
                pass

    def subscribe(self, job_id: str, *, maxsize: int = 256) -> queue.Queue[Event | None]:
        q: queue.Queue[Event | None] = queue.Queue(maxsize=maxsize)
        with self._lock:
            self._subscribers[job_id].append(q)
        return q

    def unsubscribe(self, job_id: str, q: queue.Queue[Event | None]) -> None:
        with self._lock:
            if job_id in self._subscribers:
                self._subscribers[job_id] = [
                    item for item in self._subscribers[job_id] if item is not q
                ]

    def close(self, job_id: str) -> None:
        with self._lock:
            subs = list(self._subscribers.get(job_id, []))
        for sub in subs:
            try:
                sub.put_nowait(None)
            except queue.Full:
                pass


job_events = JobEventBus()
