# Архитектура AiCursach

## Обзор

Один репозиторий — один продукт. Корень содержит инфраструктуру и общие каталоги; **`backend/`** — Python backend (src layout).

| Путь | Назначение |
|------|------------|
| `backend/src/backend/` | Backend: api, domain, application, infrastructure |
| `backend/tests/` | Тесты backend |
| `frontend/` | React UI |
| `tools/` | docx, диаграммы, scaffold |
| `data/` | Runtime (jobs, projects) |
| `scripts/` | setup, start-db, build |
| `deploy/` | Docker |

## Структура корня

```
AiCursach/
├── .gitignore
├── .env.example
├── pyproject.toml
├── Dockerfile
├── backend/
│   ├── src/backend/        # python -m backend
│   └── tests/
├── frontend/
├── tools/
├── data/
├── static/dist/
├── scripts/
├── deploy/
└── docs/
```

## backend — Clean Architecture

```
backend/src/backend/
├── core/           # config, paths, bootstrap (composition helpers)
├── domain/         # entities, rules, ports (Protocol) — без I/O
├── application/    # use cases, container (composition root)
├── infrastructure/ # adapters: DB, LangGraph, filesystem, LLM
├── api/            # FastAPI routes, HTTP → use cases
└── __main__.py
```

### Правила зависимостей

| Слой | Может импортировать |
|------|---------------------|
| `domain` | только stdlib / другой `domain` |
| `application` | `domain`, порты через `container` |
| `infrastructure` | `domain`, `core`, внешние библиотеки |
| `api` | `application`, `domain` (DTO) |
| `core` | env, пути — не бизнес-логика |

**Composition root:** `application/container.py` — единственное место, где `application` связывает порты с адаптерами.

### Domain ports (`domain/ports/`)

| Порт | Назначение |
|------|------------|
| `JobRepository` | CRUD задач, шаги, черновики, ZIP в БД |
| `WorkflowEngine` | LangGraph stream / resume / rerun |
| `EventPublisher` | SSE-события по job_id |
| `TokenMetricsStore` | учёт токенов LLM |
| `DoiTitleResolver` | Crossref по DOI |
| `FileTextExtractor` | текст из upload (docx/pdf/…) |
| `CheckpointerInfo` | имя бэкенда checkpointer |
| `JobContextScope` | contextvar job_id для адаптеров |
| `AppSettings` | read-only настройки из `.env` |
| `ProjectWorkspace` | per-job workspace: scaffold, ZIP, snapshots |

`tools/` вызывается только из `infrastructure/adapters/`.

## Frontend — Clean Architecture

```
frontend/src/
├── app/              # App.tsx, роутинг
├── presentation/     # React UI (pages, panels, components)
├── application/      # hooks, view models, container
├── domain/           # types, pure helpers (без fetch)
└── infrastructure/   # HTTP clients, gateways
```

### Правила зависимостей

| Слой | Может импортировать |
|------|---------------------|
| `domain` | только типы / pure functions |
| `application` | `domain`, порты; инфра — через `container` |
| `presentation` | `application`, `domain` |
| `infrastructure` | `domain`, fetch-клиенты |

**Composition root:** `application/container.ts` — `jobGateway`, `jobFeaturesGateway`, `graphGateway`.
Application hooks talk only to these ports; `infrastructure/api/*` is reached via `httpJobGateway` adapters.
ESLint enforces the boundary (`npm run lint` in `frontend/`).

## tools/ — библиотека оформления

- `common/` — docx по СТП
- `diagrams/` — PlantUML, IDEF0
- `scaffold/` — init_project.py

## Запуск

| Команда | Действие |
|---------|----------|
| `bash start-web.sh` | Полный dev-стек |
| `bash scripts/setup_venv.sh` | venv + `pip install -e .` |
| `bash scripts/start-db.sh` | PostgreSQL |
| `python -m backend` | Backend |

## Тесты

```bash
.venv/bin/pytest backend/tests/ -q
cd frontend && npm run build
```

## Куда класть новый код

| Задача | Путь |
|--------|------|
| Агент LangGraph | `backend/src/backend/infrastructure/langgraph/nodes/` |
| Бизнес-правило | `backend/src/backend/domain/` |
| Port (интерфейс) | `backend/src/backend/domain/ports/` |
| Adapter | `backend/src/backend/infrastructure/adapters/` |
| API endpoint | `backend/src/backend/api/routes/` + `application/` |
| React-экран | `frontend/src/presentation/pages/` |
| View model / hook | `frontend/src/application/` |
| HTTP gateway | `frontend/src/infrastructure/gateways/` |
| Утилита docx | `tools/` |
| Env-переменная | `backend/src/backend/core/config.py` + `.env.example` |
