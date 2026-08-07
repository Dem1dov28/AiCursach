# AiCursach

Мультиагентная система для **лабораторных** и **курсовых** работ: backend на LangGraph, React UI, PostgreSQL.

## Быстрый старт

```bash
bash scripts/setup_venv.sh
cp .env.example .env          # добавьте OPENROUTER_API_KEY
bash start-web.sh
```

→ http://localhost:19407

## Docker

```bash
cp .env.example .env
bash start-docker.sh
```

## Структура репозитория

```
AiCursach/                     # монорепо продукта
├── pyproject.toml             # Python-пакет backend (editable install)
├── Dockerfile
├── backend/
│   ├── src/backend/           # Python-пакет: api, domain, agents
│   └── tests/
├── frontend/                  # React UI
├── tools/                     # docx, диаграммы, scaffold
├── data/                      # runtime: jobs/, projects/
├── static/dist/               # сборка UI
├── scripts/                   # setup, start-db, build-frontend
├── deploy/                    # docker-compose
└── docs/                      # архитектура, стандарты
```

## Полезные команды

| Команда | Назначение |
|---------|------------|
| `bash start-web.sh` | PostgreSQL + UI + backend |
| `bash scripts/start-db.sh` | Только PostgreSQL |
| `bash scripts/build-frontend.sh` | Сборка React |
| `.venv/bin/python -m backend` | Backend |
| `cd frontend && npm run dev` | UI с hot reload (:5173) |
| `.venv/bin/pytest backend/tests/ -q` | Тесты |

## Scaffold проекта

```bash
python3 tools/scaffold/init_project.py ИмяПроекта
```

## Документация

- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — агенты, env, деплой
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — слои и правила кода
- [tools/README.md](tools/README.md) — docx и диаграммы
