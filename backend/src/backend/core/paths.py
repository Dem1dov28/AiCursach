"""Пути хранения проектов: серверное data/, не локальный projects/ в корне репо."""

from __future__ import annotations

import shutil
import textwrap
from contextvars import ContextVar, Token
from pathlib import Path

from backend.core.bootstrap import repo_root
from backend.core.config import DATA_DIR, USE_SERVER_STORAGE

_REPO_ROOT = repo_root()
_DATA_DIR = DATA_DIR
TOOLS_DIR = _REPO_ROOT / "tools"

_projects_root: ContextVar[Path | None] = ContextVar("projects_root", default=None)


def repo_root() -> Path:
    return _REPO_ROOT


REPO_ROOT = _REPO_ROOT
PKG_ROOT = _REPO_ROOT / "backend" / "src" / "backend"


def data_dir() -> Path:
    return _DATA_DIR


def server_projects_root() -> Path:
    """Каталог проектов на сервере (рядом с jobs/, не в корне репозитория)."""
    return _DATA_DIR / "projects"


def legacy_projects_root() -> Path:
    """Устаревший каталог в корне репо (не используется при server storage)."""
    return _DATA_DIR / "legacy_projects"


def default_projects_root() -> Path:
    root = server_projects_root() if USE_SERVER_STORAGE else legacy_projects_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_projects_root() -> Path:
    root = _projects_root.get()
    if root is not None:
        return root
    return default_projects_root()


def set_projects_root(path: Path | None) -> Token:
    if path is not None:
        path.mkdir(parents=True, exist_ok=True)
    return _projects_root.set(path)


def reset_projects_root(token: Token) -> None:
    _projects_root.reset(token)


def project_dir(project_name: str) -> Path:
    return get_projects_root() / project_name


def scaffold_project(project_name: str, *, work_type: str = "lab") -> tuple[bool, str, Path]:
    """Создать каркас projects/<имя> в текущем projects root."""
    proj = project_dir(project_name)
    is_lab = work_type != "coursework"

    if proj.exists():
        if is_lab:
            prune_lab_extras(proj)
        return True, f"Проект уже существует: {proj}", proj

    dirs = [
        proj / "Отчет",
        proj / "Материалы" / "Диаграммы" / "puml",
        proj / "Материалы" / "Диаграммы" / "png",
        proj / "Материалы" / "Скриншоты",
        proj / "src",
    ]
    if not is_lab:
        dirs.append(proj / "Скрипты")

    for folder in dirs:
        folder.mkdir(parents=True, exist_ok=True)

    if not is_lab:
        (proj / "README.md").write_text(
            textwrap.dedent(
                f"""\
                # {project_name}

                Сгенерировано AiCursach (серверное хранилище).
                """
            ),
            encoding="utf-8",
        )
        (proj / "Скрипты" / "content.py").write_text(
            '"""Сгенерировано AiCursach."""\nTOPIC = ""\n',
            encoding="utf-8",
        )

    return True, f"Создано: {proj}", proj


def prune_lab_extras(proj: Path) -> None:
    """Убрать служебные файлы, не нужные студенту в лабораторной."""
    readme = proj / "README.md"
    if readme.is_file():
        readme.unlink()
    scripts = proj / "Скрипты"
    if scripts.is_dir():
        shutil.rmtree(scripts, ignore_errors=True)


def lab_zip_skip(path: Path, project_root: Path) -> bool:
    """Исключить из ZIP лабораторной служебные пути."""
    rel = path.relative_to(project_root)
    parts = rel.parts
    if rel.name == "README.md":
        return True
    return len(parts) > 0 and parts[0] == "Скрипты"
