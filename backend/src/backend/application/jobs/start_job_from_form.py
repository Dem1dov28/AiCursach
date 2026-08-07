"""Use case: validate form uploads and build CreateJobInput."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.application.jobs.create_job import CreateJob, CreateJobInput
from backend.application.uploads.parse_upload import parse_upload_bytes
from backend.domain.document.materials_classify import classify_materials
from backend.domain.workflow.variant_select import build_assignment_context


@dataclass(frozen=True)
class JobFormFiles:
    assignment_data: bytes = b""
    assignment_name: str = ""
    assignment_text: str = ""
    example_data: bytes = b""
    example_name: str = ""
    methodical_data: bytes = b""
    methodical_name: str = ""
    materials: tuple[tuple[str, bytes], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class JobFormMeta:
    work_type: str = "auto"
    project_name: str = "MyWork"
    student_info: str = ""
    student_group: str = ""
    student_name: str = ""
    teacher_name: str = ""
    assignment_variant: str = ""
    topic: str = ""


def _parse_material_items(
    materials: tuple[tuple[str, bytes], ...],
) -> tuple[list[tuple[str, str]], list[str]]:
    items: list[tuple[str, str]] = []
    errors: list[str] = []
    for name, data in materials:
        text, _, err = parse_upload_bytes(data, name)
        if err and not text.strip():
            errors.append(f"{name}: {err}")
            continue
        if text.strip():
            items.append((name, text.strip()))
    return items, errors


class StartJobFromForm:
    def __init__(self) -> None:
        self._create = CreateJob()

    def execute(self, files: JobFormFiles, meta: JobFormMeta) -> tuple[str, str]:
        errors: list[str] = []

        material_items, material_errors = _parse_material_items(files.materials)
        errors.extend(material_errors)

        file_text, assignment_name, assignment_err = "", "", None
        if files.assignment_data:
            assignment_name = files.assignment_name or "assignment"
            file_text, _, assignment_err = parse_upload_bytes(
                files.assignment_data,
                assignment_name,
            )

        pasted = files.assignment_text.strip()
        variant = meta.assignment_variant.strip()

        explicit_assignment = ""
        if pasted:
            explicit_assignment = pasted
        elif file_text.strip():
            explicit_assignment = file_text

        explicit_example = ""
        if files.example_data:
            example_name = files.example_name or "example"
            example_parsed, _, example_err = parse_upload_bytes(files.example_data, example_name)
            if example_err and not example_parsed.strip():
                errors.append(example_err)
            else:
                explicit_example = example_parsed.strip()
                material_items.append((example_name, explicit_example))

        explicit_methodical = ""
        if files.methodical_data:
            methodical_name = files.methodical_name or "methodical"
            methodical_parsed, _, methodical_err = parse_upload_bytes(
                files.methodical_data,
                methodical_name,
            )
            if methodical_err and not methodical_parsed.strip():
                errors.append(f"Методичка: {methodical_err}")
            elif methodical_parsed.strip():
                explicit_methodical = methodical_parsed.strip()
                material_items.append((methodical_name, explicit_methodical))

        if assignment_err and not pasted and not material_items:
            errors.append(assignment_err)

        classified = classify_materials(
            material_items,
            explicit_assignment=explicit_assignment,
            explicit_example=explicit_example,
            explicit_methodical=explicit_methodical,
        )

        assignment_body = classified.assignment_text
        if not assignment_body.strip():
            errors.append(
                "Загрузите материалы (задание, методичку, пример) или вставьте текст задания."
            )

        example_text = classified.example_text.strip() or (
            "(отдельный пример не загружен — определи структуру и оформление "
            "из методички и других материалов)"
        )
        methodical_text = classified.methodical_text
        materials_bundle = classified.materials_bundle_text
        materials_roles = classified.roles

        if errors:
            raise ValueError(" ".join(errors))

        work_type = "auto" if meta.work_type in ("custom",) else (
            meta.work_type if meta.work_type in ("lab", "coursework", "auto") else "auto"
        )

        safe_name = "".join(c for c in meta.project_name if c.isalnum() or c in "_-")[:40] or "MyWork"

        assignment_ctx = build_assignment_context(
            assignment_body,
            variant=variant,
            methodical_text=methodical_text or materials_bundle,
        )

        return self._create.execute(
            CreateJobInput(
                work_type=work_type,
                project_name=safe_name,
                assignment_text=assignment_ctx["assignment_text"],
                assignment_full_text=assignment_ctx["assignment_full_text"],
                general_requirements_text=assignment_ctx["general_requirements_text"],
                variant_task_text=assignment_ctx["variant_task_text"],
                assignment_variant=variant,
                example_text=example_text,
                example_bytes=files.example_data,
                example_filename=files.example_name or "example",
                assignment_bytes=files.assignment_data,
                assignment_filename=assignment_name,
                methodical_text=methodical_text,
                methodical_bytes=files.methodical_data,
                methodical_filename=files.methodical_name,
                materials_bundle_text=materials_bundle,
                materials_roles=materials_roles,
                student_info=meta.student_info,
                student_group=meta.student_group.strip(),
                student_name=meta.student_name.strip(),
                teacher_name=meta.teacher_name.strip(),
                topic=meta.topic.strip(),
            )
        )
