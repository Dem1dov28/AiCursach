#!/usr/bin/env python3
"""PlantUML (.puml → .png) + опционально IDEF0/БД из tools/diagrams."""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
JAR = TOOLS / "jars" / "plantuml.jar"
PLANTUML_URL = "https://github.com/plantuml/plantuml/releases/download/v1.2024.7/plantuml-1.2024.7.jar"


def ensure_jar() -> Path:
    JAR.parent.mkdir(parents=True, exist_ok=True)
    if not JAR.exists():
        print("Скачивание plantuml.jar...")
        urllib.request.urlretrieve(PLANTUML_URL, JAR)
    return JAR


def render_puml(puml_dir: Path, out_dir: Path) -> int:
    puml_dir = puml_dir.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(puml_dir.glob("*.puml"))
    if not files:
        print(f"Нет .puml в {puml_dir}")
        return 1
    jar = ensure_jar()
    cmd = ["java", "-jar", str(jar), "-tpng", "-o", str(out_dir)] + [str(f) for f in files]
    subprocess.run(cmd, check=True)
    print(f"PNG → {out_dir} ({len(files)} файлов)")
    return 0


def render_extras() -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from idef0_draw import run as idef0_run

        idef0_run()
        print("IDEF0: готово")
    except Exception as e:
        print(f"IDEF0 пропущен: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puml", type=Path, default=Path("Материалы/Диаграммы/puml"))
    ap.add_argument("--out", type=Path, default=Path("Материалы/Диаграммы/png"))
    ap.add_argument("--extras", action="store_true", help="IDEF0, ER (нужна настройка в скриптах)")
    args = ap.parse_args()
    rc = render_puml(args.puml, args.out)
    if args.extras:
        render_extras()
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
