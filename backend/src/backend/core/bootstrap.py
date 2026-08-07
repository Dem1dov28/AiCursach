"""Bootstrap Python path for AiCursach and the tools library."""

from __future__ import annotations

import sys
from pathlib import Path

_ENV_LOADED = False


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "backend" / "src" / "backend" / "__main__.py").is_file() and (
            parent / "tools" / "diagrams" / "idef0_draw.py"
        ).is_file():
            return parent
    return here.parents[4]


def pkg_root() -> Path:
    return repo_root() / "backend" / "src" / "backend"


def ensure_repo_on_path() -> Path:
    root = repo_root()
    src = root / "backend" / "src"
    for entry in (str(src), str(root)):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    return root


def load_env() -> Path:
    """Load `.env` from repository root (once). Falls back to legacy `backend/.env`."""
    global _ENV_LOADED
    root = repo_root()
    if _ENV_LOADED:
        return root

    from dotenv import load_dotenv

    primary = root / ".env"
    if primary.is_file():
        load_dotenv(primary, override=False)
    else:
        legacy = root / "backend" / ".env"
        if legacy.is_file():
            load_dotenv(legacy, override=False)

    _ENV_LOADED = True
    return root
