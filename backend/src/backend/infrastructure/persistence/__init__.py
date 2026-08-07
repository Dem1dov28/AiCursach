"""Персистентное хранилище задач (PostgreSQL)."""

from backend.domain.jobs.records import JobRecord
from backend.infrastructure.persistence.job_store import JobStore, get_job_store, reset_job_store

__all__ = ["JobRecord", "JobStore", "get_job_store", "reset_job_store"]
