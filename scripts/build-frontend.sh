#!/usr/bin/env bash
# Сборка React UI (Vite) → static/dist
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "⚠ npm не найден — пропуск сборки frontend"
  exit 0
fi

cd "$FRONTEND"
if [[ -f package-lock.json ]]; then
  npm ci --silent
else
  npm install --silent
fi
npm run build
echo "✓ Frontend собран: static/dist"
