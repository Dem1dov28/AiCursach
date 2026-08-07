"""Генерация и рендер PlantUML / IDEF0 в projects/*/Материалы/Диаграммы."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from backend.infrastructure.adapters.idef0_spec import render_idef0

from backend.core.paths import REPO_ROOT as ROOT, TOOLS_DIR, project_dir
from backend.infrastructure.adapters.text_utils import as_text


def diagram_dirs(project_name: str) -> tuple[Path, Path]:
    base = project_dir(project_name) / "Материалы" / "Диаграммы"
    puml = base / "puml"
    png = base / "png"
    puml.mkdir(parents=True, exist_ok=True)
    png.mkdir(parents=True, exist_ok=True)
    return puml, png


def save_plantuml_files(project_name: str, files: list[dict]) -> list[str]:
    puml_dir, _ = diagram_dirs(project_name)
    saved: list[str] = []
    for item in files:
        name = item.get("filename", "diagram.puml")
        if not name.endswith(".puml"):
            name += ".puml"
        content = item.get("content", "")
        if "@startuml" not in content:
            content = f"@startuml\n{content}\n@enduml"
        path = puml_dir / name
        path.write_text(content, encoding="utf-8")
        saved.append(str(path.relative_to(ROOT)))
    return saved


def render_plantuml(project_name: str) -> tuple[bool, str, list[str]]:
    puml_dir, png_dir = diagram_dirs(project_name)
    files = sorted(puml_dir.glob("*.puml"))
    if not files:
        return True, "Нет .puml для рендера", []

    code, out = _run_render(puml_dir, png_dir)
    pngs = [str(p.relative_to(ROOT)) for p in sorted(png_dir.glob("*.png"))]
    ok = code == 0 and (not files or len(pngs) >= len(files))
    if ok:
        return True, out or f"PNG: {len(pngs)} файлов", pngs
    return False, out or "PlantUML: ошибка рендера", pngs


def _run_render(puml_dir: Path, png_dir: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [
            sys.executable,
            str(TOOLS_DIR / "diagrams" / "render_diagrams.py"),
            "--puml",
            str(puml_dir.relative_to(ROOT)),
            "--out",
            str(png_dir.relative_to(ROOT)),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def png_paths(files: list[str]) -> list[str]:
    """Только визуальные артефакты (.png) — .puml без рендера не считаются готовыми."""
    return [f for f in files if str(f).lower().endswith(".png")]


def apply_diagram_package(
    project_name: str,
    package: dict,
) -> tuple[list[str], list[str], bool, str]:
    """Сохранить PlantUML + IDEF0, отрендерить. Возвращает (файлы, лог, render_ok, render_error)."""
    logs: list[str] = []
    all_files: list[str] = []

    plantuml = package.get("plantuml") or []
    if plantuml:
        saved = save_plantuml_files(project_name, plantuml)
        all_files.extend(saved)
        logs.append(f"PlantUML: {len(saved)} файлов")

    idef0 = package.get("idef0")
    if idef0:
        _, png_dir = diagram_dirs(project_name)
        idef0_pngs = render_idef0(idef0, png_dir)
        rel = [str(Path(p).relative_to(ROOT)) for p in idef0_pngs]
        all_files.extend(rel)
        logs.append(f"IDEF0: {len(idef0_pngs)} PNG")

    render_ok = True
    render_error = ""

    if plantuml:
        ok, msg, pngs = render_plantuml(project_name)
        all_files.extend(pngs)
        logs.append(msg if ok else f"Ошибка PlantUML: {msg}")
        render_ok = ok
        if not ok:
            render_error = msg

    return all_files, logs, render_ok, render_error


def diagrams_render_success(
    package: dict,
    *,
    all_files: list[str],
    render_ok: bool,
) -> bool:
    """Done только при реальных PNG; одного .puml недостаточно."""
    pngs = png_paths(all_files)
    if not pngs:
        return False
    if package.get("plantuml"):
        return bool(render_ok)
    if package.get("idef0"):
        return True
    return False
