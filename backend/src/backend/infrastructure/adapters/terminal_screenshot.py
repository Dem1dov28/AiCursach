"""Скриншоты консольных программ из настоящего терминала (macOS Terminal / script PTY)."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from backend.core.paths import project_dir

CAPTURE_DELAY_SEC = 2.5
_TERMINAL_FONTS = (
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
)
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\].*?\x07")


def _screenshots_dir(project_name: str) -> Path:
    out = project_dir(project_name) / "Материалы" / "Скриншоты"
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_terminal_script(cwd: Path, steps: list[tuple[str, list[str]]]) -> str:
    """Собрать bash-скрипт с командами как в терминале ($ prompt)."""
    lines = [
        "#!/bin/bash",
        "export PS1=''",
        f"cd {shlex.quote(str(cwd.resolve()))}",
        "clear",
    ]
    for display, argv in steps:
        shown = display if display.lstrip().startswith("$") else f"$ {display}"
        lines.append(f"echo {shlex.quote(shown)}")
        if argv:
            lines.append(shlex.join(argv))
        lines.append("echo")
    lines.append("sleep 1")
    return "\n".join(lines) + "\n"


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def _load_terminal_font():
    from PIL import ImageFont

    for path in _TERMINAL_FONTS:
        try:
            return ImageFont.truetype(path, 14)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_terminal_transcript(text: str, out_png: Path) -> bool:
    """Fallback: отрисовка PTY-транскрипта в стиле тёмного терминала."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    cleaned = _strip_ansi(text)
    lines = [ln.rstrip() for ln in cleaned.splitlines() if ln.strip()][-50:]
    if not lines:
        return False

    bg = (28, 28, 28)
    fg = (230, 230, 230)
    prompt_color = (120, 220, 120)
    error_color = (255, 120, 120)

    line_h = 20
    pad = 14
    width = 980
    height = min(1200, pad * 2 + line_h * len(lines))
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    font = _load_terminal_font()

    y = pad
    for line in lines:
        lower = line.lower()
        if line.strip().startswith("$"):
            color = prompt_color
        elif "error:" in lower or "cannot find symbol" in lower:
            color = error_color
        else:
            color = fg
        draw.text((pad, y), line[:130], fill=color, font=font)
        y += line_h

    img.save(out_png)
    return out_png.is_file() and out_png.stat().st_size > 500


def _capture_macos_terminal(script_path: Path, out_png: Path) -> bool:
    """Скриншот окна Terminal.app на macOS."""
    if sys.platform != "darwin":
        return False
    if not shutil.which("osascript") or not shutil.which("screencapture"):
        return False

    posix_path = str(script_path.resolve())
    applescript = f'''
set scriptPath to {shlex.quote(posix_path)}
tell application "Terminal"
    activate
    do script "bash " & quoted form of scriptPath
    delay {CAPTURE_DELAY_SEC}
    set winID to id of front window
end tell
return winID
'''
    try:
        proc = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if proc.returncode != 0:
            return False
        win_id = (proc.stdout or "").strip()
        if not win_id.isdigit():
            return False

        cap = subprocess.run(
            ["screencapture", "-x", "-l", win_id, str(out_png)],
            capture_output=True,
            timeout=20,
        )
        subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "Terminal" to close front window saving no',
            ],
            capture_output=True,
            timeout=10,
        )
        return cap.returncode == 0 and out_png.is_file() and out_png.stat().st_size > 800
    except (OSError, subprocess.TimeoutExpired):
        return False


def _capture_via_python_pty(cwd: Path, script_path: Path, out_png: Path) -> bool:
    """PTY через Python — работает в Docker/Linux без GUI."""
    import pty
    import select

    master: int | None = None
    try:
        master, slave = pty.openpty()
        proc = subprocess.Popen(
            ["bash", str(script_path)],
            cwd=cwd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            text=False,
            env={**os.environ, "TERM": "xterm-256color"},
        )
        os.close(slave)
        chunks: list[bytes] = []
        while True:
            ready, _, _ = select.select([master], [], [], 0.25)
            if ready:
                try:
                    chunk = os.read(master, 8192)
                except OSError:
                    break
                if chunk:
                    chunks.append(chunk)
            elif proc.poll() is not None:
                while True:
                    try:
                        chunk = os.read(master, 8192)
                    except OSError:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                break
        proc.wait(timeout=60)
        text = b"".join(chunks).decode("utf-8", errors="replace")
        return _render_terminal_transcript(text, out_png)
    except (OSError, subprocess.TimeoutExpired):
        return False
    finally:
        if master is not None:
            try:
                os.close(master)
            except OSError:
                pass


def _capture_via_script_pty(cwd: Path, script_path: Path, out_png: Path) -> bool:
    """Fallback: запись сессии через /usr/bin/script (настоящий PTY)."""
    if not shutil.which("script"):
        return False

    transcript = script_path.with_suffix(".typescript")
    try:
        subprocess.run(
            ["script", "-q", str(transcript), "bash", str(script_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "TERM": "xterm-256color"},
        )
        if not transcript.is_file():
            return False
        text = transcript.read_text(encoding="utf-8", errors="replace")
        return _render_terminal_transcript(text, out_png)
    except (OSError, subprocess.TimeoutExpired):
        return False
    finally:
        transcript.unlink(missing_ok=True)


def capture_terminal_session(
    project_name: str,
    cwd: Path,
    steps: list[tuple[str, list[str]]],
) -> Path | None:
    """Скриншот выполнения: macOS Terminal → Python PTY → script → PNG."""
    if not steps:
        return None

    dest = _screenshots_dir(project_name)
    script_path = dest / "_terminal_capture.sh"
    out_png = dest / "02_console.png"

    script_path.write_text(build_terminal_script(cwd, steps), encoding="utf-8")
    script_path.chmod(0o755)

    if _capture_macos_terminal(script_path, out_png):
        return out_png
    if _capture_via_python_pty(cwd, script_path, out_png):
        return out_png
    if _capture_via_script_pty(cwd, script_path, out_png):
        return out_png
    return None
