# AiCursach — production (API + компиляторы + Chromium)
# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent 2>/dev/null || npm install --silent
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=19407 \
    AICURSACH_DATA_DIR=/app/data \
    AICURSACH_USE_SERVER_STORAGE=1 \
    DATABASE_URL=postgresql://bsuir:bsuir@postgres:5432/bsuir_work \
    CHROME_PATH=/usr/bin/chromium \
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    openjdk-17-jdk-headless \
    chromium \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend/src backend/src
RUN pip install --upgrade pip && pip install -e .

COPY tools/ tools/
COPY deploy/ deploy/
COPY scripts/ scripts/
COPY --from=frontend /src/static/dist static/dist

RUN mkdir -p data/jobs data/projects \
    && chmod +x deploy/docker-entrypoint.sh

EXPOSE 19407

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:19407/api/health', timeout=3)"

ENTRYPOINT ["deploy/docker-entrypoint.sh"]
CMD ["serve"]
