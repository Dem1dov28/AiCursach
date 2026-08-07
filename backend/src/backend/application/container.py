"""Composition root — wire domain ports to infrastructure."""

from __future__ import annotations

from backend.core.config import AppConfig, get_config
from backend.domain.ports.app_settings import AppSettings
from backend.domain.ports.checkpointer_info import CheckpointerInfo
from backend.domain.ports.doi_resolver import DoiTitleResolver
from backend.domain.ports.event_publisher import EventPublisher
from backend.domain.ports.file_extractor import FileTextExtractor
from backend.domain.ports.job_context_scope import JobContextScope
from backend.domain.ports.job_repository import JobRepository
from backend.domain.ports.token_metrics import TokenMetricsStore
from backend.domain.ports.project_workspace import ProjectWorkspace
from backend.domain.ports.workflow_engine import WorkflowEngine
from backend.infrastructure.adapters.crossref_client import fetch_crossref_title
from backend.infrastructure.adapters.file_extract import extract_text_or_hint
from backend.infrastructure.adapters.project_workspace import FilesystemProjectWorkspace
from backend.infrastructure.context.job_context import reset_job_id, set_job_id
from backend.infrastructure.events.job_event_bus import job_events
from backend.infrastructure.langgraph.checkpointer import checkpointer_backend
from backend.infrastructure.langgraph.workflow_graph import get_workflow_app
from backend.infrastructure.metrics.token_accounting import token_accounting
from backend.infrastructure.persistence.job_store import get_job_store

_workspace: FilesystemProjectWorkspace | None = None


class _ConfigAppSettings:
    """Adapter: core AppConfig → AppSettings port."""

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg

    @property
    def graph_recursion_limit(self) -> int:
        return self._cfg.graph_recursion_limit

    @property
    def max_revisions(self) -> int:
        return self._cfg.max_revisions

    @property
    def data_dir(self):
        return self._cfg.data_dir

    @property
    def crossref_verify(self) -> bool:
        return self._cfg.crossref_verify


class _FileTextExtractorAdapter:
    def extract(self, data: bytes, filename: str) -> tuple[str, str]:
        return extract_text_or_hint(data, filename)


class _CheckpointerInfoAdapter:
    def backend_name(self) -> str:
        return checkpointer_backend()


class _JobContextScopeAdapter:
    def set_job_id(self, job_id: str | None):
        return set_job_id(job_id)

    def reset_job_id(self, token) -> None:
        reset_job_id(token)


def job_repository() -> JobRepository:
    return get_job_store()


def workflow_engine() -> WorkflowEngine:
    return get_workflow_app()


def event_publisher() -> EventPublisher:
    return job_events


def token_metrics() -> TokenMetricsStore:
    return token_accounting


def doi_title_resolver() -> DoiTitleResolver:
    return fetch_crossref_title


def file_text_extractor() -> FileTextExtractor:
    return _FileTextExtractorAdapter()


def checkpointer_info() -> CheckpointerInfo:
    return _CheckpointerInfoAdapter()


def job_context_scope() -> JobContextScope:
    return _JobContextScopeAdapter()


def app_settings() -> AppSettings:
    return _ConfigAppSettings(get_config())


def project_workspace() -> ProjectWorkspace:
    global _workspace
    if _workspace is None:
        cfg = get_config()
        _workspace = FilesystemProjectWorkspace(
            data_dir=cfg.data_dir,
            job_repository=job_repository(),
            resolve_doi_title=doi_title_resolver(),
        )
    return _workspace


def bootstrap_application() -> None:
    """Initialize persistence, checkpointer, and workflow graph once at startup."""
    from backend.infrastructure.langgraph.checkpointer import init_checkpointer
    from backend.infrastructure.langgraph.workflow_graph import reset_workflow_app

    job_repository().init_schema()
    init_checkpointer()
    reset_workflow_app()
