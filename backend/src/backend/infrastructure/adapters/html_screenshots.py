"""Скриншоты HTML/JS-проектов для раздела «Работа программы»."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from backend.core.config import get_config
from backend.core.paths import REPO_ROOT as ROOT, project_dir


def _run(cmd: list[str], *, timeout: int = 45) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return -1, "таймаут"
    except FileNotFoundError as exc:
        return -1, str(exc)


def _find_chrome() -> str | None:
    env_path = get_config().chrome_path
    if env_path and Path(env_path).exists():
        return env_path
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


def _chrome_extra_flags() -> list[str]:
    import shlex

    raw = get_config().chromium_flags
    flags = shlex.split(raw) if raw else []
    if "--no-sandbox" not in flags:
        flags.append("--no-sandbox")
    if "--disable-dev-shm-usage" not in flags:
        flags.append("--disable-dev-shm-usage")
    return flags


def _screenshots_dir(project_name: str) -> Path:
    out = project_dir(project_name) / "Материалы" / "Скриншоты"
    out.mkdir(parents=True, exist_ok=True)
    return out


def find_main_html(src: Path) -> Path | None:
    for rel in ("html/index.html", "index.html", "html/main.html"):
        path = src / rel
        if path.is_file():
            return path
    html_files = sorted(src.rglob("*.html"))
    return html_files[0] if html_files else None


def screenshot_page(html_path: Path, out_png: Path, *, width: int = 1280, height: int = 900) -> bool:
    chrome = _find_chrome()
    if not chrome:
        return False
    url = html_path.resolve().as_uri()
    code, _ = _run(
        [
            chrome,
            *_chrome_extra_flags(),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            f"--window-size={width},{height}",
            f"--screenshot={out_png.resolve()}",
            url,
        ],
        timeout=60,
    )
    return code == 0 and out_png.is_file() and out_png.stat().st_size > 0


_RESULT_PAGE_STEMS = ("result", "results", "output", "preview", "success", "response")


_FAILURE_OUTPUT_MARKERS = (
    "error:",
    "cannot find symbol",
    "package org.apache",
    "package does not exist",
    "traceback (most recent call last)",
    "exception in thread",
    "compilation failed",
    "npm err",
    "syntaxerror",
    "no such file or directory",
    "command not found",
    "jdk не найден",
)


def looks_like_failure_output(text: str) -> bool:
    """Вывод компилятора/ошибки — не подходит для рисунка «работа программы»."""
    sample = (text or "").strip().lower()
    if not sample:
        return False
    return any(marker in sample for marker in _FAILURE_OUTPUT_MARKERS)


def _remove_console_screenshot(project_name: str) -> None:
    path = _screenshots_dir(project_name) / "02_console.png"
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


def _is_html_project_output(output: str) -> bool:
    text = (output or "").strip().lower()
    return text.startswith("html-проект") or "html/css/js" in text


def _skip_console_screenshot(
    *,
    code_language: str,
    console_output: str,
    has_html_shots: bool,
    code_run_success: bool | None = None,
) -> bool:
    lang = (code_language or "").lower()
    if lang in ("javascript", "js", "html", "web"):
        return True
    if has_html_shots:
        return True
    if code_run_success is False:
        return True
    if looks_like_failure_output(console_output):
        return True
    return _is_html_project_output(console_output)


def _is_valid_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 64:
        return False
    try:
        head = path.read_bytes()[:12]
    except OSError:
        return False
    if not (
        head.startswith(b"\x89PNG\r\n\x1a\n")
        or head[:3] == b"\xff\xd8\xff"
        or head[:6] in (b"GIF87a", b"GIF89a")
    ):
        return False
    try:
        from PIL import Image

        with Image.open(path) as im:
            w, h = im.size
        return w >= 200 and h >= 200
    except Exception:
        return True


def _copy_existing_pngs(project_name: str, dest: Path) -> list[Path]:
    src_root = project_dir(project_name) / "src"
    copied: list[Path] = []
    if not src_root.is_dir():
        return copied
    idx = 10
    for path in sorted(src_root.rglob("*.png")):
        if not _is_valid_image(path):
            continue
        target = dest / f"{idx:02d}_{path.stem}.png"
        if not target.exists():
            shutil.copy2(path, target)
        copied.append(target)
        idx += 1
    return copied


def render_console_screenshot(project_name: str, output: str) -> Path | None:
    """Устаревший fallback: если терминальный скриншот не создан, отрисовать вывод."""
    text = (output or "").strip()
    if not text or looks_like_failure_output(text):
        return None

    dest = _screenshots_dir(project_name)
    out_png = dest / "02_console.png"
    if out_png.is_file() and out_png.stat().st_size > 800:
        return out_png

    from backend.infrastructure.adapters.terminal_screenshot import _render_terminal_transcript

    transcript = f"$ ./program\n{text}"
    if _render_terminal_transcript(transcript, out_png):
        return out_png if _is_valid_image(out_png) else None
    return None


def _is_result_page(path: Path) -> bool:
    stem = path.stem.lower()
    return any(token in stem for token in _RESULT_PAGE_STEMS)


def _list_html_pages(src: Path) -> list[Path]:
    if not src.is_dir():
        return []
    main = find_main_html(src)
    pages: list[Path] = []
    if main:
        pages.append(main)
    for path in sorted(src.rglob("*.html")):
        if path not in pages and _is_result_page(path):
            pages.append(path)
    for path in sorted(src.rglob("*.html")):
        if path not in pages:
            pages.append(path)
    return pages[:5]


def capture_html_screenshots(project_name: str) -> tuple[list[Path], str]:
    """Скриншоты HTML-страниц + копирование PNG из src/."""
    dest = _screenshots_dir(project_name)
    src = project_dir(project_name) / "src"
    logs: list[str] = []
    shots: list[Path] = []

    html_pages = _list_html_pages(src)
    for i, html in enumerate(html_pages, 1):
        out_png = dest / f"{i:02d}_{html.stem}.png"
        shot_height = 1600 if i == 1 else 900
        if screenshot_page(html, out_png, height=shot_height):
            shots.append(out_png)
            logs.append(f"Скриншот: {html.name}")
        elif i == 1:
            logs.append("Headless Chrome недоступен — скриншот HTML не сделан")

    copied = _copy_existing_pngs(project_name, dest)
    for path in copied:
        if path not in shots:
            shots.append(path)
    if copied:
        logs.append(f"Скопировано PNG из src/: {len(copied)}")

    if not shots:
        return [], "; ".join(logs) or "Нет скриншотов"

    shots = sorted({p.resolve() for p in shots}, key=lambda p: p.name)
    return shots, "; ".join(logs)


def collect_program_screenshots(
    project_name: str,
    *,
    console_output: str = "",
    code_language: str = "",
    code_run_success: bool | None = None,
) -> tuple[list[Path], str]:
    """Все скриншоты для раздела «Работа программы»."""
    if code_run_success is False or looks_like_failure_output(console_output):
        _remove_console_screenshot(project_name)

    shots, logs = capture_html_screenshots(project_name)
    has_html_shots = bool(shots)

    skip_console = _skip_console_screenshot(
        code_language=code_language,
        console_output=console_output,
        has_html_shots=has_html_shots,
        code_run_success=code_run_success,
    )

    if not skip_console and console_output.strip():
        dest = _screenshots_dir(project_name)
        existing = dest / "02_console.png"
        if existing.is_file() and _is_valid_image(existing):
            if existing not in shots:
                shots.append(existing)
                logs = f"{logs}; терминал" if logs else "терминал"
        else:
            console_png = render_console_screenshot(project_name, console_output)
            if console_png and console_png not in shots:
                shots.append(console_png)
                logs = f"{logs}; консольный вывод" if logs else "консольный вывод"

    dest = _screenshots_dir(project_name)
    if dest.is_dir():
        for path in sorted(dest.glob("*.png")):
            if path.name == "02_console.png" and skip_console:
                continue
            if path not in shots and _is_valid_image(path):
                shots.append(path)

    if not shots:
        return [], logs or "Нет скриншотов"

    if skip_console:
        shots = [path for path in shots if path.name != "02_console.png"]

    shots = sorted({p.resolve() for p in shots}, key=lambda p: p.name)
    return shots, logs
