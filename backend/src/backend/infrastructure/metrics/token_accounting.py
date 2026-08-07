"""Infrastructure: accumulate LLM token usage per job."""

from __future__ import annotations

import threading
from typing import Any

from backend.core.config import get_config
from backend.domain.metrics.token_usage import SessionMetrics, TokenUsage
from backend.infrastructure.context.job_context import get_job_id

_DEFAULT_INPUT_USD = 0.40 / 1_000_000
_DEFAULT_OUTPUT_USD = 1.60 / 1_000_000


def _price_per_token(kind: str) -> float:
    cfg = get_config()
    if kind == "input":
        return cfg.llm_input_usd_per_token if cfg.llm_input_usd_per_token is not None else _DEFAULT_INPUT_USD
    return cfg.llm_output_usd_per_token if cfg.llm_output_usd_per_token is not None else _DEFAULT_OUTPUT_USD


class TokenAccountingService:
    """Thread-safe in-memory ledger keyed by job id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics: dict[str, SessionMetrics] = {}

    def record(self, job_id: str, usage: TokenUsage, *, agent: str | None = None) -> SessionMetrics:
        cost = (
            usage.input_tokens * _price_per_token("input")
            + usage.output_tokens * _price_per_token("output")
        )
        delta = SessionMetrics.from_usage(usage, cost_usd=cost, agent=agent)
        with self._lock:
            current = self._metrics.get(job_id, SessionMetrics.empty())
            merged = current.merge(delta)
            self._metrics[job_id] = merged
            return merged

    def record_current(self, usage: TokenUsage, *, agent: str | None = None) -> SessionMetrics | None:
        job_id = get_job_id()
        if not job_id:
            return None
        return self.record(job_id, usage, agent=agent)

    def get(self, job_id: str) -> SessionMetrics:
        with self._lock:
            return self._metrics.get(job_id, SessionMetrics.empty())

    def to_state_patch(self, job_id: str) -> dict[str, Any]:
        return self.get(job_id).to_dict()

    def clear(self, job_id: str) -> None:
        with self._lock:
            self._metrics.pop(job_id, None)


token_accounting = TokenAccountingService()
