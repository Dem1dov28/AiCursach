"""Use case: create and start a new job."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from backend.application.jobs.job_executor import save_job_inputs, start_job
from backend.application.container import job_repository, app_settings


@dataclass(frozen=True)
class CreateJobInput:
    work_type: str
    project_name: str
    assignment_text: str
    example_text: str
    topic: str = ""
    methodical_text: str = ""
    assignment_variant: str = ""
    assignment_full_text: str = ""
    general_requirements_text: str = ""
    variant_task_text: str = ""
    student_info: str = ""
    student_group: str = ""
    student_name: str = ""
    teacher_name: str = ""
    example_bytes: bytes = b""
    example_filename: str = ""
    assignment_bytes: bytes = b""
    assignment_filename: str = ""
    methodical_bytes: bytes = b""
    methodical_filename: str = ""
    materials_bundle_text: str = ""
    materials_roles: dict[str, str] | None = None
    custom_pipeline: list[str] | None = None


class CreateJob:
    def execute(self, data: CreateJobInput) -> tuple[str, str]:
        store = job_repository()
        job_id = uuid.uuid4().hex[:12]
        record = store.create_job(
            job_id,
            project_name=data.project_name,
            work_type=data.work_type,
        )

        save_job_inputs(
            job_id,
            assignment_text=data.assignment_text,
            assignment_filename=data.assignment_filename,
            assignment_bytes=data.assignment_bytes,
            example_text=data.example_text,
            example_filename=data.example_filename,
            example_bytes=data.example_bytes,
            methodical_text=data.methodical_text,
            methodical_filename=data.methodical_filename,
            methodical_bytes=data.methodical_bytes,
        )

        start_job(
            job_id=job_id,
            work_type=data.work_type,
            project_name=data.project_name,
            assignment_text=data.assignment_text,
            example_text=data.example_text,
            topic=data.topic,
            methodical_text=data.methodical_text,
            assignment_variant=data.assignment_variant,
            assignment_full_text=data.assignment_full_text,
            general_requirements_text=data.general_requirements_text,
            variant_task_text=data.variant_task_text,
            student_info=data.student_info,
            student_group=data.student_group,
            student_name=data.student_name,
            teacher_name=data.teacher_name,
            example_bytes=data.example_bytes,
            example_filename=data.example_filename,
            materials_bundle_text=data.materials_bundle_text,
            materials_roles=data.materials_roles or {},
            recursion_limit=app_settings().graph_recursion_limit,
            custom_pipeline=data.custom_pipeline,
        )
        return job_id, record.status
