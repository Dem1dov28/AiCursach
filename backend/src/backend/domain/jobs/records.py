"""Job persistence records (domain layer)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

JobStatus = Literal["queued", "running", "paused", "completed", "failed"]


@dataclass
class JobInputRecord:
    kind: str
    filename: str
    extracted_text: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        preview = self.extracted_text.strip()
        if len(preview) > 400:
            preview = preview[:400] + "…"
        return {
            "kind": self.kind,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "preview": preview,
            "has_binary": self.size_bytes > 0,
        }


@dataclass
class JobRecord:
    id: str
    status: JobStatus = "queued"
    created_at: str = ""
    project_name: str = ""
    work_type: str = "lab"
    final_state: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    zip_filename: str = ""
    has_zip: bool = False
    steps: list[dict[str, Any]] = field(default_factory=list)
    step_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "created_at": self.created_at,
            "project_name": self.project_name,
            "work_type": self.work_type,
            "topic": self.final_state.get("topic", ""),
            "steps": self.steps,
            "step_count": self.step_count or len(self.steps),
            "error": self.error,
            "has_download": self.has_zip,
            "output_docx": self.final_state.get("output_docx_path", ""),
            "code_ok": self.final_state.get("code_run_success", False),
            "diagrams_count": len(self.final_state.get("diagram_files", [])),
            "storage": "postgresql",
            "custom_pipeline": self.final_state.get("custom_pipeline") or [],
        }
