"""Pure mapping: agent node output → user-facing step message."""

from __future__ import annotations

from backend.domain.shared.text import as_text


def step_message(node: str, output: dict) -> tuple[str, str]:
    if node == "breakpoint":
        return (
            output.get("current_sub_task", "Точка останова"),
            "Утвердите план работы перед запуском Писателя",
        )
    if node == "supervisor":
        return (
            output.get("current_sub_task", "Маршрутизация"),
            f"→ {output.get('next_step', '')}",
        )
    if node == "analyzer":
        return (
            f"Тема: {output.get('topic', '')}",
            as_text(output.get("requirements", ""))[:300],
        )
    if node == "researcher":
        findings = output.get("research_findings", [])
        return ("Теория собрана", findings[-1][:300] if findings else "")
    if node == "writer":
        return ("Черновик готов", "")
    if node == "bibliography_verifier":
        verified = output.get("bibliography_verified")
        n = len(output.get("citation_issues") or [])
        return (f"Источники: {'OK' if verified else 'есть замечания'}", f"замечаний: {n}")
    if node == "style_polisher":
        n = len(output.get("style_issues") or [])
        return ("Стиль отполирован", f"осталось клише: {n}")
    if node == "project_init":
        return ("Каркас проекта", output.get("project_path", "")[:200])
    if node == "coder_gen":
        ok = output.get("code_generated")
        return (f"Генерация кода: {'OK' if ok else 'ошибка'}", "")
    if node == "code_runner":
        ok = output.get("code_run_success")
        return (
            f"Запуск кода: {'OK' if ok else 'ошибка'}",
            output.get("code_run_output", "")[:300],
        )
    if node == "diagrammer":
        n = len(output.get("diagram_files", []))
        return (f"Диаграммы: {n} файлов", "")
    if node == "assets_builder":
        logs = output.get("tool_log", [])
        return ("Подготовка Excel/графиков", logs[-1] if logs else "")
    if node == "antiplagiat":
        logs = output.get("tool_log", [])
        return ("Антиплагиат", logs[-1] if logs else "")
    if node == "annex_builder":
        logs = output.get("tool_log", [])
        return ("План приложений", logs[-1] if logs else "")
    if node == "docx_builder":
        logs = output.get("tool_log", [])
        path = output.get("output_docx_path", "")
        return ("Сборка docx", path or (logs[-1] if logs else ""))
    if node == "critiquer":
        rerun = output.get("critique_rerun", "")
        note = output.get("critique_notes", "")[:280]
        if rerun:
            return (f"Проверка → {rerun}", note)
        return ("Проверка", note)
    return (node, "")
