"""Central application settings loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from backend.core.bootstrap import load_env, repo_root

load_env()
_REPO = repo_root()


def _env_bool(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def _env_float(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        raw = os.environ.get(name, "").strip()
        if raw:
            return raw
    return default


def _env_bool_first(default: str, *names: str) -> bool:
    for name in names:
        if name in os.environ:
            return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")
    return default.strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True, slots=True)
class AppConfig:
    web_host: str
    web_port: int
    graph_recursion_limit: int
    max_revisions: int
    data_dir: Path
    use_server_storage: bool
    database_url: str

    openrouter_api_key: str
    openai_api_key: str
    openrouter_model: str
    openai_model: str
    openrouter_base_url: str
    openrouter_site_url: str
    openrouter_app_name: str
    openai_base_url: str

    crossref_verify: bool
    tavily_api_key: str
    openalex_mailto: str
    semantic_scholar_api_key: str

    chrome_path: str
    chromium_flags: str
    llm_input_usd_per_token: float | None
    llm_output_usd_per_token: float | None

    @classmethod
    def from_env(cls) -> AppConfig:
        data_dir = Path(
            _env_first("AICURSACH_DATA_DIR", "WORK_ASSISTANT_DATA_DIR", default=str(_REPO / "data"))
        )
        return cls(
            web_host=os.environ.get("WEB_HOST", "0.0.0.0"),
            web_port=int(os.environ.get("WEB_PORT", "19407")),
            graph_recursion_limit=int(os.environ.get("GRAPH_RECURSION_LIMIT", "80")),
            max_revisions=int(os.environ.get("MAX_REVISIONS", "3")),
            data_dir=data_dir,
            use_server_storage=_env_bool_first(
                "1",
                "AICURSACH_USE_SERVER_STORAGE",
                "WORK_ASSISTANT_USE_SERVER_STORAGE",
            ),
            database_url=os.environ.get(
                "DATABASE_URL",
                "postgresql://bsuir:bsuir@localhost:54329/bsuir_work",
            ),
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", "").strip(),
            openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            openrouter_base_url=os.environ.get(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            openrouter_site_url=os.environ.get("OPENROUTER_SITE_URL", ""),
            openrouter_app_name=os.environ.get("OPENROUTER_APP_NAME", "AiCursach"),
            openai_base_url=os.environ.get("OPENAI_BASE_URL", "").strip(),
            crossref_verify=_env_bool("CROSSREF_VERIFY", "1"),
            tavily_api_key=os.environ.get("TAVILY_API_KEY", "").strip(),
            openalex_mailto=os.environ.get("OPENALEX_MAILTO", "bsuir-tools@local").strip(),
            semantic_scholar_api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip(),
            chrome_path=os.environ.get("CHROME_PATH", "").strip(),
            chromium_flags=os.environ.get("CHROMIUM_FLAGS", "").strip(),
            llm_input_usd_per_token=_env_float("LLM_INPUT_USD_PER_TOKEN"),
            llm_output_usd_per_token=_env_float("LLM_OUTPUT_USD_PER_TOKEN"),
        )

    def llm_api_key(self) -> str:
        return self.openrouter_api_key or self.openai_api_key

    def llm_configured(self) -> bool:
        return bool(self.llm_api_key())

    def uses_openrouter(self) -> bool:
        return bool(self.openrouter_api_key)

    def llm_model(self) -> str:
        return self.openrouter_model if self.uses_openrouter() else self.openai_model

    def llm_base_url(self) -> str | None:
        if self.uses_openrouter():
            return self.openrouter_base_url
        return self.openai_base_url or None

    def web_url(self) -> str:
        host = "localhost" if self.web_host in ("0.0.0.0", "::") else self.web_host
        return f"http://{host}:{self.web_port}"

    def openrouter_referer(self) -> str:
        return self.openrouter_site_url or self.web_url()


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig.from_env()


# Backward-compatible module-level constants (read once at import).
_cfg = get_config()
WEB_HOST = _cfg.web_host
WEB_PORT = _cfg.web_port
GRAPH_RECURSION_LIMIT = _cfg.graph_recursion_limit
MAX_REVISIONS = _cfg.max_revisions
DATA_DIR = _cfg.data_dir
USE_SERVER_STORAGE = _cfg.use_server_storage
DATABASE_URL = _cfg.database_url


def web_url() -> str:
    return get_config().web_url()
