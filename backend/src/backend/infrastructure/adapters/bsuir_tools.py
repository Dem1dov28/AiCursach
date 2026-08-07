"""Обёртки над инструментами репозитория (tools/)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.core.paths import REPO_ROOT as ROOT, TOOLS_DIR, project_dir, scaffold_project
from backend.infrastructure.adapters.text_utils import as_text


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def init_project(project_name: str, *, work_type: str = "lab") -> tuple[bool, str, Path]:
    return scaffold_project(project_name, work_type=work_type)


def write_coursework_content_py(
    project_name: str,
    payload: dict,
    *,
    student_group: str = "",
    student_name: str = "",
    teacher_name: str = "",
    discipline: str = "",
    variant: str = "",
) -> tuple[bool, str, Path]:
    proj = project_dir(project_name)
    scripts = proj / "Скрипты"
    scripts.mkdir(parents=True, exist_ok=True)
    content_path = scripts / "content.py"

    intro = payload.get("intro", [])
    sections = payload.get("sections", [])
    conclusion = payload.get("conclusion", [])
    sources = payload.get("sources", [])
    topic = payload.get("topic", "Тема курсового проекта")
    referat = payload.get("referat") if isinstance(payload.get("referat"), dict) else {}

    group = (student_group or "473601").strip() or "473601"
    student = (student_name or "И. С. Студент").strip() or "И. С. Студент"
    teacher = (teacher_name or "Преподаватель").strip() or "Преподаватель"
    disc = (discipline or payload.get("discipline") or "Дисциплина")
    disc = as_text(disc) if not isinstance(disc, str) else disc.strip() or "Дисциплина"
    try:
        variant_num = int(str(variant).strip() or "1")
    except ValueError:
        variant_num = 1

    goal = as_text(referat.get("goal") or "цель работы")
    methodology = as_text(referat.get("methodology") or "методология")
    results = as_text(referat.get("results") or "результаты")
    keywords = as_text(referat.get("keywords") or "КЛЮЧЕВОЕ, СЛОВО")
    tech_stack = as_text(referat.get("tech_stack") or "стек технологий")
    application = as_text(referat.get("application") or "область применения")
    try:
        originality_pct = int(referat.get("originality_pct") or 92)
    except (TypeError, ValueError):
        originality_pct = 92
    originality_pct = max(50, min(99, originality_pct))

    def _q(text: str) -> str:
        return text.replace('"', "'")

    lines = [
        '"""Сгенерировано AiCursach."""',
        "from tools.common.referat import ReferatConfig",
        "",
        f'TOPIC = "«{_q(as_text(topic))}»"',
        'DOC_CODE = "БГУИР КП 6-05-0611-01 010 ПЗ"',
        f'DISCIPLINE = "{_q(disc)}"',
        f"VARIANT = {variant_num}",
        f'GROUP = "{_q(group)}"',
        f'STUDENT = "{_q(student)}"',
        f'TEACHER = "{_q(teacher)}"',
        "",
        "REFERAT = ReferatConfig(",
        f'    topic_title="{_q(as_text(topic))}",',
        f'    keywords_caps="{_q(keywords)}",',
        f'    goal="{_q(goal)}",',
        f'    methodology="{_q(methodology)}",',
        f'    results="{_q(results)}",',
        f'    tech_stack="{_q(tech_stack)}",',
        f'    application="{_q(application)}",',
        f"    originality_pct={int(originality_pct)},",
        ")",
        "",
        "TOC_ENTRIES = [",
        '    ("Введение", 0, 5),',
    ]
    page = 7
    for sec in sections:
        title = as_text(sec.get("title", "Раздел"))
        lines.append(f'    ("{title.replace(chr(34), chr(39))}", 0, {page}),')
        page += 3
    lines.extend(
        [
            '    ("Заключение", 0, 20),',
            '    ("Список использованных источников", 0, 21),',
            "]",
            "",
            "INTRO = [",
        ]
    )
    for p in intro:
        lines.append(f'    "{as_text(p).replace(chr(34), chr(39))}",')
    lines.append("]")
    lines.append("")
    lines.append("SECTIONS = [")
    for sec in sections:
        title = as_text(sec.get("title", "РАЗДЕЛ"))
        paras = sec.get("paragraphs", [])
        lines.append(f'    ("{title.replace(chr(34), chr(39))}", [')
        for p in paras:
            lines.append(f'        "{as_text(p).replace(chr(34), chr(39))}",')
        lines.append("    ]),")
    lines.append("]")
    lines.append("")
    lines.append("CONCLUSION = [")
    for p in conclusion:
        lines.append(f'    "{as_text(p).replace(chr(34), chr(39))}",')
    lines.append("]")
    lines.append("")
    lines.append("SOURCES = [")
    for s in sources:
        lines.append(f'    "{as_text(s).replace(chr(34), chr(39))}",')
    lines.append("]")
    lines.append("")

    content_path.write_text("\n".join(lines), encoding="utf-8")
    return True, f"Записан content.py: {content_path}", content_path


def build_coursework_report(project_name: str) -> tuple[bool, str, Path | None]:
    proj = project_dir(project_name)
    build_script = proj / "Скрипты" / "build_report.py"
    if not build_script.exists():
        ok, _, _ = init_project(project_name)
        if not ok:
            return False, "Не удалось создать scaffold", None

    code, out = _run([sys.executable, str(build_script.relative_to(ROOT))])
    out_path = proj / "Отчет" / "Пояснительная_записка.docx"
    if code == 0 and out_path.exists():
        return True, out, out_path
    return False, out, out_path if out_path.exists() else None


def render_diagrams(project_name: str) -> tuple[bool, str]:
    puml = project_dir(project_name) / "Материалы" / "Диаграммы" / "puml"
    png = project_dir(project_name) / "Материалы" / "Диаграммы" / "png"
    if not any(puml.glob("*.puml")):
        return True, "Нет .puml файлов — пропуск render_diagrams"
    puml.mkdir(parents=True, exist_ok=True)
    png.mkdir(parents=True, exist_ok=True)
    code, out = _run(
        [
            sys.executable,
            str(TOOLS_DIR / "diagrams" / "render_diagrams.py"),
            "--puml",
            str(puml.relative_to(ROOT)),
            "--out",
            str(png.relative_to(ROOT)),
        ]
    )
    return code == 0, out


def parse_json_from_llm(text: str) -> dict | None:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None
