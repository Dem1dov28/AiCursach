"""Health check route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import get_job_repository
from backend.core.config import get_config
from backend.domain.ports.job_repository import JobRepository

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health(repo: JobRepository = Depends(get_job_repository)):
    cfg = get_config()
    db_ok = False
    db_error = ""
    try:
        db_ok = repo.ping()
    except Exception as exc:
        db_error = str(exc)
    return {
        "ok": db_ok and cfg.llm_configured(),
        "llm_configured": cfg.llm_configured(),
        "database": "postgresql",
        "database_ok": db_ok,
        "database_error": db_error or None,
    }
