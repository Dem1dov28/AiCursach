# Инструменты оформления (docx, диаграммы)

Библиотека внутри AiCursach. Вызывается адаптерами backend и из CLI.

## Установка

```bash
bash scripts/setup_venv.sh
```

Нужна **Java** для PlantUML.

## Scaffold

```bash
python3 tools/scaffold/init_project.py MyProject
# правите data/projects/MyProject/Скрипты/content.py
python3 data/projects/MyProject/Скрипты/build_report.py
```

## Частые команды

```bash
python3 tools/diagrams/render_diagrams.py \
  --puml data/projects/MyProject/Материалы/Диаграммы/puml \
  --out data/projects/MyProject/Материалы/Диаграммы/png

python3 tools/common/update_toc.py data/projects/MyProject/Отчет/Пояснительная_записка.docx
```

## Структура

| Папка | Назначение |
|-------|------------|
| `common/` | СТП, титул, реферат, оглавление |
| `diagrams/` | PlantUML, IDEF0, блок-схемы |
| `scaffold/` | Каркас новой работы |
| `coursework/` | Excel, графики |
| `labs/`, `contracts/`, `posters/` | Спец. шаблоны |

Образец оформления: `docs/standards/СТП 2024.pdf`.
