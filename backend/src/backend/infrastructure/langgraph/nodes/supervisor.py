"""Supervisor — координатор workflow."""

from __future__ import annotations

from backend.domain.workflow.custom_pipeline import MAX_CODER_GEN_ATTEMPTS
from backend.domain.workflow.revision_limit import effective_max_revisions
from backend.domain.workflow.rerun import (
    build_rerun_patches,
    normalize_revision_target,
    normalize_rerun_target,
)
from backend.domain.workflow.work_state import WorkState


def _needs_coursework_assets(state: WorkState) -> bool:
    return bool(state.get("needs_charts") or state.get("needs_excel"))


def _revision_patches(target: str) -> dict:
    patches: dict = {"critique_rerun": ""}
    if target in ("writer", "bibliography_verifier", "style_polisher", "docx_builder", "assets_builder", "annex_builder", "antiplagiat", "coder_gen", "code_runner", "diagrammer"):
        patches["output_docx_path"] = ""
    if target in ("writer", "bibliography_verifier", "style_polisher"):
        patches["bibliography_verified"] = False
        patches["style_polished"] = False
        patches["bibliography_attempts"] = 0
        patches["style_polisher_attempts"] = 0
    if target == "assets_builder":
        patches["coursework_assets_done"] = False
        patches["assets_builder_attempts"] = 0
        patches["assets_quality"] = ""
    if target == "annex_builder":
        patches["annex_plan_done"] = False
        patches["annex_builder_attempts"] = 0
        patches["annex_plan"] = ""
    if target == "antiplagiat":
        patches["antiplagiat_done"] = False
        patches["antiplagiat_attempts"] = 0
        patches["antiplagiat_screenshot"] = ""
        patches["annex_reserved_letters"] = []
    if target == "coder_gen":
        patches["code_generated"] = False
        patches["code_run_done"] = False
        patches["coder_gen_attempts"] = 0
    if target == "code_runner":
        patches["code_run_done"] = False
    if target == "diagrammer":
        patches["diagrams_generated"] = False
        patches["diagrammer_attempts"] = 0
    return patches


def supervisor_node(state: WorkState) -> dict:
    from backend.domain.workflow.custom_pipeline import custom_supervisor_next, normalize_custom_pipeline

    pipeline = normalize_custom_pipeline(state.get("custom_pipeline"))
    if pipeline and state.get("requirements"):
        return custom_supervisor_next(state)

    if state.get("work_type") == "custom":
        return custom_supervisor_next(state)

    force = state.get("force_rerun", "")
    if force:
        target = normalize_rerun_target(force)
        return {
            "next_step": target,
            "force_rerun": "",
            "current_sub_task": f"Повторный запуск ({target})",
            **build_rerun_patches(target, set_force_flag=False),
        }

    has_analysis = bool(state.get("requirements"))
    has_research = bool(state.get("research_findings"))
    has_draft = bool(state.get("content_draft", "").strip())
    has_build = bool(state.get("output_docx_path"))
    critique = state.get("critique_notes", "")
    revision = state.get("revision_number", 0)
    max_revisions = effective_max_revisions(state)

    needs_code = bool(state.get("needs_code", False))
    needs_diagrams = bool(state.get("needs_diagrams", False))
    code_generated = state.get("code_generated", False)
    code_run_done = state.get("code_run_done", False)
    diagrams_done = state.get("diagrams_generated", False)
    project_ready = state.get("project_initialized", False)
    assets_done = state.get("coursework_assets_done", False)

    if "APPROVED" in critique.upper() and has_build:
        return {
            "next_step": "END",
            "current_sub_task": "Работа завершена и одобрена",
        }

    if critique and "APPROVED" not in critique.upper() and revision < max_revisions:
        target = normalize_revision_target(state.get("critique_rerun") or "writer")
        return {
            "next_step": target,
            "revision_number": revision + 1,
            "current_sub_task": f"Доработка ({target}) по замечаниям критика",
            **_revision_patches(target),
        }

    if revision >= max_revisions and critique and "APPROVED" not in critique.upper():
        return {
            "next_step": "END",
            "current_sub_task": "Достигнут лимит ревизий — финализация",
        }

    if not has_analysis:
        return {
            "next_step": "analyzer",
            "current_sub_task": "Разобрать задание и пример работы",
        }

    if not project_ready:
        return {
            "next_step": "project_init",
            "current_sub_task": "Создать каркас проекта",
        }

    if not has_research:
        return {
            "next_step": "researcher",
            "current_sub_task": f"Найти теорию и источники по теме: {state.get('topic', '')}",
        }

    if not has_draft:
        return {
            "next_step": "writer",
            "current_sub_task": "Сгенерировать черновик контента",
        }

    if needs_code and not code_generated:
        attempts = int(state.get("coder_gen_attempts") or 0)
        if attempts < MAX_CODER_GEN_ATTEMPTS:
            return {
                "next_step": "coder_gen",
                "current_sub_task": f"Сгенерировать код ({state.get('code_language', 'python')})",
            }

    if needs_code and code_run_done and not state.get("code_run_success"):
        retries = int(state.get("code_auto_retries") or 0)
        if retries < 1:
            return {
                "next_step": "coder_gen",
                "code_auto_retries": retries + 1,
                "code_generated": False,
                "code_run_done": False,
                "output_docx_path": "",
                "current_sub_task": "Перегенерация Java-кода после ошибки компиляции",
            }

    if needs_code and not code_run_done:
        return {
            "next_step": "code_runner",
            "current_sub_task": f"Запустить код ({state.get('code_language', 'python')})",
        }

    if needs_diagrams and not diagrams_done:
        return {
            "next_step": "diagrammer",
            "current_sub_task": "Сгенерировать PlantUML и IDEF0 диаграммы",
        }

    if _needs_coursework_assets(state) and not assets_done:
        return {
            "next_step": "assets_builder",
            "current_sub_task": "Подготовить Excel и графики",
        }

    if state.get("needs_antiplagiat") and not state.get("antiplagiat_done"):
        return {
            "next_step": "antiplagiat",
            "current_sub_task": "Антиплагиат / оригинальность",
        }

    if state.get("needs_annexes") and not state.get("annex_plan_done"):
        return {
            "next_step": "annex_builder",
            "current_sub_task": "Спланировать приложения",
        }

    if not has_build:
        return {
            "next_step": "docx_builder",
            "current_sub_task": "Собрать docx через инструменты tools/",
        }

    if not critique:
        return {
            "next_step": "critiquer",
            "current_sub_task": "Проверить качество и соответствие СТП",
        }

    return {
        "next_step": "critiquer",
        "current_sub_task": "Повторная проверка",
    }
