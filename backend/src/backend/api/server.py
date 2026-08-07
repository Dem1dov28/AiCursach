"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from backend.core.bootstrap import ensure_repo_on_path, load_env, repo_root

ensure_repo_on_path()
load_env()

from backend.application.container import bootstrap_application
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes.graph import router as graph_router
from backend.api.routes.health import router as health_router
from backend.api.routes.jobs import router as jobs_router

REPO_ROOT = repo_root()
STATIC_DIR = REPO_ROOT / "static"
DIST_DIR = STATIC_DIR / "dist"
SPA_INDEX = DIST_DIR / "index.html"

# HTML must not be cached — after `npm run build` chunk hashes change.
_SPA_INDEX_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
}


def _spa_index_response() -> HTMLResponse:
    if not SPA_INDEX.is_file():
        raise HTTPException(
            503,
            "Frontend не собран. Выполните: bash scripts/build-frontend.sh",
        )
    return HTMLResponse(
        SPA_INDEX.read_text(encoding="utf-8"),
        headers=_SPA_INDEX_HEADERS,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap_application()
    yield


app = FastAPI(title="AiCursach", version="1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(graph_router)
app.include_router(jobs_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if SPA_INDEX.is_file():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse)
async def index():
    return _spa_index_response()


@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_fallback(full_path: str):
    """React Router — отдаём index.html для client-side маршрутов (/workbench, …)."""
    blocked_prefixes = ("api/", "static/", "assets/")
    blocked_exact = {"docs", "redoc", "openapi.json"}
    if full_path.startswith(blocked_prefixes) or full_path in blocked_exact:
        raise HTTPException(status_code=404)
    return _spa_index_response()
