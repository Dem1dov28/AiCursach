#!/usr/bin/env bash
# PostgreSQL (Docker) + сборка UI + backend AiCursach.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

bash scripts/start-db.sh

if [[ ! -x .venv/bin/python ]]; then
  echo "→ venv не найден, запуск setup_venv.sh…"
  bash scripts/setup_venv.sh
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Создан .env — добавьте OPENROUTER_API_KEY"
fi

bash scripts/build-frontend.sh

exec .venv/bin/python -m backend
