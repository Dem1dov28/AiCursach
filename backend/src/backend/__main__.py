"""Run the web server: python -m backend"""

from __future__ import annotations

import sys


def _check_deps() -> None:
    missing = []
    for mod in ("langgraph", "fastapi", "uvicorn", "dotenv", "psycopg"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print("Не установлены зависимости:", ", ".join(missing))
        print(f"Python: {sys.executable}")
        print("Выполните: bash scripts/setup_venv.sh")
        print("Запускайте: python -m backend")
        raise SystemExit(1)


def main() -> None:
    _check_deps()
    from backend.core.bootstrap import load_env

    load_env()
    import uvicorn

    from backend.core.config import WEB_HOST, WEB_PORT, web_url
    from backend.api.server import app

    print(f"Python: {sys.executable}")
    print(f"AiCursach → {web_url()}")
    uvicorn.run(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
