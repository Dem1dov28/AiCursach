#!/usr/bin/env bash
# Пересоздание venv и установка зависимостей (нужен Python 3.12 или 3.13)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

PY=""
for candidate in python3.12 python3.13 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    major=${ver%%.*}
    minor=${ver#*.}
    if [ "$major" -eq 3 ] && [ "$minor" -ge 12 ] && [ "$minor" -le 13 ]; then
      PY=$candidate
      break
    fi
  fi
done

if [ -z "$PY" ]; then
  echo "Нужен Python 3.12 или 3.13 (brew install python@3.12)"
  exit 1
fi

echo "Python: $($PY --version)"
rm -rf .venv
"$PY" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pip install "gostdoc @ git+https://github.com/samikofficial/gostdoc.git"
echo ""
echo "Готово. Запуск:"
echo "  bash start-web.sh"
echo "  # или: .venv/bin/python -m backend"
