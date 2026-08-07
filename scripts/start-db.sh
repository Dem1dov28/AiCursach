#!/usr/bin/env bash
# Запуск PostgreSQL в Docker (обязателен для Work Assistant).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/../deploy" && pwd)"
cd "$DEPLOY_DIR"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-bsuir-work-postgres}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker не найден. Установите Docker Desktop: https://www.docker.com/products/docker-desktop/"
  exit 1
fi

COMPOSE=(docker compose)
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
fi

container_exists() {
  docker ps -a --format '{{.Names}}' | grep -qx "$POSTGRES_CONTAINER"
}

container_running() {
  docker ps --format '{{.Names}}' | grep -qx "$POSTGRES_CONTAINER"
}

echo "→ PostgreSQL (Docker)…"

if container_exists; then
  if container_running; then
    echo "   контейнер $POSTGRES_CONTAINER уже запущен"
  else
    echo "   запуск существующего контейнера $POSTGRES_CONTAINER…"
    docker start "$POSTGRES_CONTAINER" >/dev/null
  fi
else
  if ! "${COMPOSE[@]}" up -d postgres; then
    # Race or orphan from other compose project — reuse by name if it appeared.
    if container_exists; then
      docker start "$POSTGRES_CONTAINER" >/dev/null 2>&1 || true
    else
      echo ""
      echo "Не удалось создать PostgreSQL. Если контейнер остался от старого запуска:"
      echo "  docker rm -f $POSTGRES_CONTAINER"
      echo "  bash scripts/start-db.sh"
      exit 1
    fi
  fi
fi

echo -n "→ Ожидание готовности БД"
for _ in $(seq 1 40); do
  if docker exec "$POSTGRES_CONTAINER" pg_isready -U bsuir -d bsuir_work >/dev/null 2>&1; then
    echo " OK"
    echo "DATABASE_URL=postgresql://bsuir:bsuir@localhost:54329/bsuir_work"
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo ""
echo "PostgreSQL не ответил вовремя. Логи:"
docker logs "$POSTGRES_CONTAINER" --tail 20 2>&1 || "${COMPOSE[@]}" logs postgres --tail 20
exit 1
