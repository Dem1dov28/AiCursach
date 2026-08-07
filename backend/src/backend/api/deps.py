"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException

from backend.application.container import job_repository
from backend.core.config import get_config
from backend.domain.ports.job_repository import JobRepository


def require_llm_configured() -> None:
    if not get_config().llm_configured():
        raise HTTPException(
            503,
            "Не задан OPENROUTER_API_KEY или OPENAI_API_KEY. Добавьте ключ в .env в корне репозитория.",
        )


def get_job_repository() -> JobRepository:
    return job_repository()
