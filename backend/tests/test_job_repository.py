"""JobRepository port conformance."""

from backend.domain.ports.job_repository import JobRepository
from backend.infrastructure.persistence.job_store import JobStore


def test_job_store_implements_job_repository_protocol():
    store = JobStore(url="postgresql://bsuir:bsuir@localhost:54329/bsuir_work")
    assert isinstance(store, JobRepository)
