"""Интеграция с tools/coursework: Excel и графики."""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

from backend.core.paths import REPO_ROOT as ROOT, TOOLS_DIR, project_dir

CW = TOOLS_DIR / "coursework"

IOUZ_MARKERS = (
    "иоуз",
    "abc",
    "xyz",
    "eoq",
    "запас",
    "номенклатур",
    "склад",
    "материальн",
)


def _iouz_data_ready() -> bool:
    required = [
        CW / "приложение_А_исходные_данные_50.tsv",
        CW / "результаты_ABC_XYZ.tsv",
        CW / "матрица_ABC_XYZ.tsv",
    ]
    return all(p.exists() for p in required)


def _run_script(name: str) -> tuple[bool, str]:
    script = CW / name
    if not script.exists():
        return False, f"Нет скрипта {name}"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=CW,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out.strip()[:2000]


def _copy_tree(src: Path, dst: Path, pattern: str = "*") -> list[str]:
    dst.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    if not src.exists():
        return copied
    for item in sorted(src.glob(pattern)):
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
        copied.append(str(target.relative_to(ROOT)))
    return copied


def run_iouz_toolkit(project_name: str) -> tuple[list[str], list[str]]:
    """Полный pipeline ИОУЗ, если есть TSV/XLSX в tools/coursework."""
    logs: list[str] = []
    artifacts: list[str] = []
    proj = project_dir(project_name)

    if not _iouz_data_ready():
        logs.append("ИОУЗ: нет TSV-данных в tools/coursework — пропуск")
        return artifacts, logs

    steps = [
        ("build_excel_with_formulas.py", "Excel с формулами"),
        ("build_excel_files.py", "Экспорт листов Excel"),
        ("generate_charts.py", "Графики PNG"),
    ]
    for script, label in steps:
        ok, out = _run_script(script)
        logs.append(f"{label}: {'OK' if ok else 'ошибка'}")
        if out:
            logs.append(out[:400])

    excel_dst = proj / "Материалы" / "Excel"
    charts_dst = proj / "Материалы" / "Графики"
    artifacts.extend(_copy_tree(CW / "excel", excel_dst, "*.xlsx"))
    artifacts.extend(_copy_tree(CW / "excel", excel_dst, "*.txt"))
    master = CW / "таблицы_для_курсовой.xlsx"
    if master.exists():
        excel_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy2(master, excel_dst / master.name)
        artifacts.append(str((excel_dst / master.name).relative_to(ROOT)))

    charts_src = CW / "word_assets_final"
    artifacts.extend(_copy_tree(charts_src, charts_dst, "*.png"))
    return artifacts, logs


def _generate_simple_charts(project_name: str, topic: str) -> list[str]:
    """Устаревший placeholder (dummy). Не использовать для quality-success."""
    return []


def render_topic_assets(
    project_name: str,
    package: dict,
) -> tuple[list[str], list[str]]:
    """TSV + графики из нормализованного LLM-пакета."""
    from backend.domain.document.asset_package import normalize_asset_package

    logs: list[str] = []
    artifacts: list[str] = []
    data = normalize_asset_package(package)
    charts = data.get("charts") or []
    table = data.get("table")

    if table and table.get("rows"):
        tsv = write_sample_data_tsv(project_name, table["rows"])
        if tsv:
            artifacts.append(tsv)
            logs.append(f"TSV: {tsv} ({len(table['rows'])} строк)")

    if not charts:
        logs.append("Нет валидных charts в package")
        return artifacts, logs

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        from tools.coursework.generate_charts import bar_chart, line_chart, pie_chart
        import tools.coursework.generate_charts as gc
    except ImportError as exc:
        logs.append(f"generate_charts недоступен: {exc}")
        return artifacts, logs

    out_dir = project_dir(project_name) / "Материалы" / "Графики"
    out_dir.mkdir(parents=True, exist_ok=True)
    gc.OUT = out_dir

    for chart in charts:
        name = chart["filename"]
        labels = chart["labels"]
        values = chart["values"]
        try:
            kind = chart["type"]
            if kind == "bar":
                bar_chart(
                    labels,
                    values,
                    chart.get("ylabel") or "Показатель",
                    name,
                    xlabel=chart.get("xlabel") or "",
                )
            elif kind == "line":
                line_chart(
                    labels,
                    values,
                    chart.get("ylabel") or "Показатель",
                    name,
                    xlabel=chart.get("xlabel") or "Период",
                )
            elif kind == "pie":
                pie_chart(labels, [max(1, int(round(v))) for v in values], name)
            else:
                continue
            path = out_dir / name
            if path.exists():
                artifacts.append(str(path.relative_to(ROOT)))
                logs.append(f"График {kind}: {name}")
        except Exception as exc:
            logs.append(f"Ошибка {name}: {exc}")

    return artifacts, logs


def prepare_coursework_assets(
    project_name: str,
    *,
    topic: str = "",
    requirements: str = "",
    use_iouz: bool | None = None,
    package: dict | None = None,
) -> tuple[list[str], list[str], str]:
    """Excel + графики в projects/<name>/Материалы/.

    Returns:
        artifacts, logs, mode — ``iouz`` | ``topic`` | ``placeholder`` | ``none``
    """
    req_l = (requirements + " " + topic).lower()
    wants_iouz = use_iouz if use_iouz is not None else any(m in req_l for m in IOUZ_MARKERS)

    if wants_iouz and _iouz_data_ready():
        artifacts, logs = run_iouz_toolkit(project_name)
        mode = "iouz" if artifacts else "none"
        return artifacts, logs, mode

    if package:
        artifacts, logs = render_topic_assets(project_name, package)
        pngs = [a for a in artifacts if str(a).lower().endswith(".png")]
        if pngs:
            logs.append(f"Topic-driven: {len(pngs)} PNG")
            return artifacts, logs, "topic"
        logs.append("Topic-driven: PNG не созданы")
        return artifacts, logs, "none"

    logs = ["Нет IOUZ-данных и нет topic-package — assets не сгенерированы"]
    return [], logs, "none"


def write_sample_data_tsv(project_name: str, rows: list[dict[str, str]]) -> str | None:
    """Опционально: сохранить табличные данные из LLM в проект."""
    if not rows:
        return None
    out = project_dir(project_name) / "Материалы" / "Данные" / "source.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return str(out.relative_to(ROOT))
