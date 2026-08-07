# Разработка AiCursach

## Python-пакет `backend/`

```
backend/
├── src/backend/
│   ├── core/             # config, paths, bootstrap
│   ├── domain/           # workflow, graph, quality, citations
│   ├── application/      # use cases (jobs, export, checkpoints)
│   ├── infrastructure/   # langgraph, adapters, persistence, llm
│   └── api/              # FastAPI REST + SPA
└── tests/
```

Установка: `pip install -e .` из корня репозитория.

## Агенты

| Агент | Роль |
|-------|------|
| **Supervisor** | Маршрутизация workflow |
| **Analyzer** | Разбор методички и задания |
| **ProjectInit** | Каркас проекта |
| **Researcher** | Теория и источники |
| **Writer** | Текст |
| **CoderGen / CodeRunner** | Код и запуск |
| **Diagrammer** | PlantUML, IDEF0 |
| **AssetsBuilder** | Excel и графики |
| **DocxBuilder** | Сборка DOCX |
| **Critiquer** | Проверка и ревизии |

## Переменные окружения (`.env` в корне)

| Переменная | Описание |
|------------|----------|
| `OPENROUTER_API_KEY` | LLM (обязательно*) |
| `DATABASE_URL` | PostgreSQL |
| `WEB_PORT` | Порт API (19407) |
| `AICURSACH_DATA_DIR` | Путь к `data/` (по умолчанию `data`) |
| `TAVILY_API_KEY` | Веб-поиск (опционально) |

\* или `OPENAI_API_KEY`

## Разработка UI

```bash
# Терминал 1
.venv/bin/python -m backend

# Терминал 2
cd frontend && npm run dev
```

→ http://localhost:5173 (прокси на :19407)

## Результат работы

Проекты в `data/projects/<Имя>/`:
- docx → `Отчет/`
- код → `src/`
- диаграммы → `Материалы/Диаграммы/`
- ZIP — из UI (PostgreSQL)

## Docker (production)

```bash
bash start-docker.sh
# или
cd deploy && docker compose up -d --build
docker compose run --rm app verify-tools
```

Образ: Python 3.12, OpenJDK 17, gcc/g++, Chromium.
