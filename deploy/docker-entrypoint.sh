#!/usr/bin/env bash
set -euo pipefail

cd /app

wait_for_db() {
  local url="${DATABASE_URL:-}"
  if [[ -z "$url" ]]; then
    echo "DATABASE_URL не задан"
    exit 1
  fi
  echo "→ Ожидание PostgreSQL…"
  for _ in $(seq 1 60); do
    if python - <<'PY'
import os, sys
import psycopg
try:
    psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=2).close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
    then
      echo "→ PostgreSQL доступен"
      return 0
    fi
    sleep 1
  done
  echo "PostgreSQL недоступен"
  exit 1
}

cmd="${1:-serve}"
shift || true

case "$cmd" in
  serve)
    wait_for_db
    exec python -m backend
    ;;
  verify-tools)
    exec python scripts/verify_code_tools.py
    ;;
  *)
    exec "$cmd" "$@"
    ;;
esac
