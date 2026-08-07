"""PostgreSQL — задачи, шаги агентов и файлы проектов."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.config import get_config
from backend.domain.jobs.records import JobInputRecord, JobRecord, JobStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    project_name TEXT NOT NULL DEFAULT '',
    work_type TEXT NOT NULL DEFAULT 'lab',
    final_state JSONB NOT NULL DEFAULT '{}',
    error TEXT NOT NULL DEFAULT '',
    zip_filename TEXT NOT NULL DEFAULT '',
    zip_data BYTEA
);
CREATE TABLE IF NOT EXISTS job_steps (
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    agent TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (job_id, step)
);
CREATE TABLE IF NOT EXISTS job_files (
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    content BYTEA NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    PRIMARY KEY (job_id, relative_path)
);
CREATE INDEX IF NOT EXISTS idx_job_steps_job ON job_steps(job_id);
CREATE INDEX IF NOT EXISTS idx_job_files_job ON job_files(job_id);
CREATE TABLE IF NOT EXISTS job_inputs (
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    filename TEXT NOT NULL DEFAULT '',
    extracted_text TEXT NOT NULL DEFAULT '',
    content BYTEA,
    PRIMARY KEY (job_id, kind)
);
CREATE TABLE IF NOT EXISTS job_draft_snapshots (
    id SERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    agent TEXT NOT NULL,
    content_draft TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_draft_snapshots_job ON job_draft_snapshots(job_id);
"""


def database_url() -> str:
    url = get_config().database_url.strip()
    if not url:
        raise RuntimeError(
            "Не задан DATABASE_URL. Запустите PostgreSQL: bash scripts/start-db.sh "
            "и скопируйте DATABASE_URL из .env.example"
        )
    if not url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError(
            f"DATABASE_URL должен указывать на PostgreSQL, получено: {url[:40]}…"
        )
    return url


class JobStore:
    """Хранилище задач в PostgreSQL."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or database_url()

    def _connect(self):
        import psycopg

        return psycopg.connect(self.url)

    def init_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                for stmt in _split_sql(_SCHEMA):
                    cur.execute(stmt)
            conn.commit()

    def ping(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() == (1,)

    def create_job(
        self,
        job_id: str,
        *,
        project_name: str,
        work_type: str,
    ) -> JobRecord:
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO jobs (id, status, created_at, project_name, work_type, final_state)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (job_id, "queued", now, project_name, work_type, "{}"),
                )
            conn.commit()
        return JobRecord(
            id=job_id,
            status="queued",
            created_at=now.isoformat(),
            project_name=project_name,
            work_type=work_type,
        )

    def update_job(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        project_name: str | None = None,
        final_state: dict | None = None,
        error: str | None = None,
    ) -> None:
        sets: list[str] = []
        values: list[Any] = []

        if status is not None:
            sets.append("status = %s")
            values.append(status)
        if project_name is not None:
            sets.append("project_name = %s")
            values.append(project_name)
        if final_state is not None:
            sets.append("final_state = %s::jsonb")
            values.append(json.dumps(final_state, ensure_ascii=False))
        if error is not None:
            sets.append("error = %s")
            values.append(error)
        if not sets:
            return

        values.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(sets)} WHERE id = %s"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(values))
            conn.commit()

    def add_step(
        self,
        job_id: str,
        *,
        step: int,
        agent: str,
        message: str,
        detail: str = "",
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_steps (job_id, step, agent, message, detail)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, step) DO UPDATE SET
                        agent = excluded.agent,
                        message = excluded.message,
                        detail = excluded.detail
                    """,
                    (job_id, step, agent, message, detail),
                )
            conn.commit()

    def save_zip(self, job_id: str, data: bytes, filename: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET zip_data = %s, zip_filename = %s WHERE id = %s",
                    (data, filename, job_id),
                )
            conn.commit()

    def import_project_files(self, job_id: str, project_dir: Path, prefix: str) -> int:
        if not project_dir.is_dir():
            return 0
        count = 0
        with self._connect() as conn:
            with conn.cursor() as cur:
                for path in project_dir.rglob("*"):
                    if not path.is_file() or ".git" in path.parts:
                        continue
                    rel = f"{prefix}/{path.relative_to(project_dir).as_posix()}"
                    cur.execute(
                        """
                        INSERT INTO job_files (job_id, relative_path, content, mime_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (job_id, relative_path) DO UPDATE SET
                            content = excluded.content,
                            mime_type = excluded.mime_type
                        """,
                        (job_id, rel, path.read_bytes(), _guess_mime(path)),
                    )
                    count += 1
            conn.commit()
        return count

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, status, created_at, project_name, work_type,
                           final_state, error, zip_filename,
                           (zip_data IS NOT NULL) AS has_zip
                    FROM jobs WHERE id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute(
                    """
                    SELECT step, agent, message, detail
                    FROM job_steps WHERE job_id = %s ORDER BY step
                    """,
                    (job_id,),
                )
                steps = [
                    {"step": s[0], "agent": s[1], "message": s[2], "detail": s[3]}
                    for s in cur.fetchall()
                ]

        fs = row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}")
        return JobRecord(
            id=row[0],
            status=row[1],
            created_at=row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
            project_name=row[3],
            work_type=row[4],
            final_state=fs,
            error=row[6] or "",
            zip_filename=row[7] or "",
            has_zip=bool(row[8]),
            steps=steps,
        )

    def get_zip(self, job_id: str) -> tuple[bytes, str] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT zip_data, zip_filename FROM jobs WHERE id = %s",
                    (job_id,),
                )
                row = cur.fetchone()
        if not row or not row[0]:
            return None
        return bytes(row[0]), row[1] or f"{job_id}.zip"

    def list_jobs(self, *, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT j.id, j.status, j.created_at, j.project_name, j.work_type,
                           j.final_state, j.error, j.zip_filename,
                           (j.zip_data IS NOT NULL) AS has_zip,
                           COALESCE(s.step_count, 0) AS step_count
                    FROM jobs j
                    LEFT JOIN (
                        SELECT job_id, COUNT(*) AS step_count
                        FROM job_steps
                        GROUP BY job_id
                    ) s ON s.job_id = j.id
                    ORDER BY j.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                rows = cur.fetchall()

        items: list[JobRecord] = []
        for row in rows:
            fs = row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}")
            items.append(
                JobRecord(
                    id=row[0],
                    status=row[1],
                    created_at=row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
                    project_name=row[3],
                    work_type=row[4],
                    final_state=fs,
                    error=row[6] or "",
                    zip_filename=row[7] or "",
                    has_zip=bool(row[8]),
                    step_count=int(row[9] or 0),
                )
            )
        return items

    def save_job_input(
        self,
        job_id: str,
        *,
        kind: str,
        filename: str,
        extracted_text: str,
        content: bytes | None = None,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_inputs (job_id, kind, filename, extracted_text, content)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, kind) DO UPDATE SET
                        filename = excluded.filename,
                        extracted_text = excluded.extracted_text,
                        content = excluded.content
                    """,
                    (job_id, kind, filename, extracted_text, content),
                )
            conn.commit()

    def get_job_inputs(self, job_id: str) -> list[JobInputRecord]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT kind, filename, extracted_text,
                           COALESCE(octet_length(content), 0) AS size_bytes
                    FROM job_inputs WHERE job_id = %s ORDER BY kind
                    """,
                    (job_id,),
                )
                rows = cur.fetchall()
        return [
            JobInputRecord(
                kind=row[0],
                filename=row[1] or "",
                extracted_text=row[2] or "",
                size_bytes=int(row[3] or 0),
            )
            for row in rows
        ]

    def restore_project_files(self, job_id: str, target_dir: Path) -> int:
        """Restore imported project files from DB to disk (for rerun)."""
        target_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT relative_path, content FROM job_files WHERE job_id = %s",
                    (job_id,),
                )
                rows = cur.fetchall()
        for rel_path, content in rows:
            if not content:
                continue
            dest = target_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(bytes(content))
            count += 1
        return count

    def add_draft_snapshot(
        self,
        job_id: str,
        *,
        step: int,
        agent: str,
        content_draft: str,
    ) -> None:
        if not content_draft.strip():
            return
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_draft_snapshots (job_id, step, agent, content_draft)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (job_id, step, agent, content_draft),
                )
            conn.commit()

    def get_draft_snapshots(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, step, agent, content_draft, created_at
                    FROM job_draft_snapshots
                    WHERE job_id = %s
                    ORDER BY id
                    """,
                    (job_id,),
                )
                rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "step": row[1],
                "agent": row[2],
                "content_draft": row[3] or "",
                "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
            }
            for row in rows
        ]

    def delete_job(self, job_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted


def _split_sql(sql: str) -> list[str]:
    return [s.strip() for s in sql.split(";") if s.strip()]


def _guess_mime(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".zip": "application/zip",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".html": "text/html",
        ".css": "text/css",
        ".js": "text/javascript",
        ".py": "text/x-python",
        ".txt": "text/plain",
        ".json": "application/json",
    }.get(ext, "application/octet-stream")


_store: JobStore | None = None
_store_lock = threading.Lock()


def get_job_store() -> JobStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = JobStore()
        return _store


def reset_job_store() -> None:
    """Clear singleton (tests only). Schema init is the app lifespan responsibility."""
    global _store
    with _store_lock:
        _store = None
