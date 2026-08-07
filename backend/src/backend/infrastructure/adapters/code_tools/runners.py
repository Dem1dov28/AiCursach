"""Запуск консольных программ (общие subprocess-хелперы)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from backend.core.paths import project_dir
from backend.infrastructure.adapters.html_screenshots import looks_like_failure_output
from backend.infrastructure.adapters.terminal_screenshot import capture_terminal_session

RUN_TIMEOUT = 30


def project_src(project_name: str) -> Path:
    src = project_dir(project_name) / "src"
    src.mkdir(parents=True, exist_ok=True)
    return src


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return -1, f"Таймаут {RUN_TIMEOUT}с"
    except FileNotFoundError as exc:
        return -1, f"Команда не найдена: {exc}"


def _run_steps(
    project_name: str,
    cwd: Path,
    steps: list[tuple[str, list[str]]],
) -> tuple[bool, str]:
    """Выполнить шаги и при успехе сделать скриншот терминала."""
    outputs: list[str] = []
    for _display, argv in steps:
        code, out = run_cmd(argv, cwd)
        if out:
            outputs.append(out)
        if code != 0:
            combined = "\n".join(outputs) if outputs else out
            return False, combined

    combined = "\n".join(outputs)
    if combined and not looks_like_failure_output(combined):
        capture_terminal_session(project_name, cwd, steps)
    return True, combined


def run_python(project_name: str, files: dict[str, str], entry_file: str) -> tuple[bool, str]:
    src = project_src(project_name)
    entry = entry_file or next(
        (n for n in files if n.endswith("main.py") or n.endswith(".py")),
        "main.py",
    )
    if not (src / entry).exists():
        py_files = list(src.glob("*.py"))
        if not py_files:
            return False, "Нет .py файлов в src/"
        entry = py_files[0].name

    steps = [(f"python3 {entry}", [sys.executable, entry])]
    return _run_steps(project_name, src, steps)


def _java_main_class(src: Path, entry_file: str, java_files: list[Path]) -> str:
    if entry_file:
        path = src / entry_file
        if path.exists():
            return _class_from_java(path)
    for candidate in ("Main.java", "App.java"):
        path = src / candidate
        if path.exists():
            return _class_from_java(path)
    for path in java_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "public static void main" in text:
            return _class_from_java(path)
    return _class_from_java(java_files[0])


def _class_from_java(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("public class "):
            return line.split()[2].split("{")[0]
    return path.stem


def run_java(project_name: str, entry_file: str) -> tuple[bool, str]:
    src = project_src(project_name)
    java_files = list(src.rglob("*.java"))
    if not java_files:
        return False, "Нет .java файлов в src/"
    javac = shutil.which("javac")
    java = shutil.which("java")
    if not javac or not java:
        return False, "JDK не найден (javac/java)"

    rel_paths = [str(f.relative_to(src)) for f in java_files]
    main_class = _java_main_class(src, entry_file, java_files)
    javac_display = "javac " + " ".join(rel_paths)
    steps = [
        (javac_display, [javac, *rel_paths]),
        (f"java {main_class}", [java, main_class]),
    ]
    return _run_steps(project_name, src, steps)


def run_c(project_name: str) -> tuple[bool, str]:
    src = project_src(project_name)
    c_files = list(src.glob("*.c"))
    if not c_files:
        return False, "Нет .c файлов в src/"
    gcc = shutil.which("gcc")
    if not gcc:
        return False, "gcc не найден"

    exe = src / ("a.out" if sys.platform != "win32" else "a.exe")
    names = [f.name for f in c_files]
    gcc_display = f"gcc -std=c11 -Wall {' '.join(names)} -o {exe.name}"
    steps = [
        (gcc_display, [gcc, "-std=c11", "-Wall", *names, "-o", exe.name]),
        (f"./{exe.name}", [str(exe)]),
    ]
    return _run_steps(project_name, src, steps)


def run_cpp(project_name: str) -> tuple[bool, str]:
    src = project_src(project_name)
    cpp_files = list(src.glob("*.cpp")) + list(src.glob("*.cc"))
    if not cpp_files:
        return False, "Нет .cpp файлов в src/"
    gpp = shutil.which("g++")
    if not gpp:
        return False, "g++ не найден"

    exe = src / ("a.out" if sys.platform != "win32" else "a.exe")
    names = [f.name for f in cpp_files]
    gpp_display = f"g++ -std=c++17 {' '.join(names)} -o {exe.name}"
    steps = [
        (gpp_display, [gpp, "-std=c++17", *names, "-o", exe.name]),
        (f"./{exe.name}", [str(exe)]),
    ]
    return _run_steps(project_name, src, steps)


def run_web(project_name: str, files: dict[str, str]) -> tuple[bool, str]:
    from backend.infrastructure.adapters.html_screenshots import capture_html_screenshots, find_main_html

    src = project_src(project_name)
    html = find_main_html(src)
    if not html and not any(n.endswith(".html") for n in files):
        return False, "Нет HTML-файлов в src/"

    _shots, msg = capture_html_screenshots(project_name)
    if html:
        rel = html.relative_to(project_dir(project_name))
        return True, f"HTML-проект: {rel}. {msg}"
    return bool(files), msg or "Файлы HTML/CSS/JS записаны"
