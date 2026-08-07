"""Pytest configuration — ensure repo root is on PYTHONPATH and .env is loaded."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
for entry in (str(SRC), str(ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from backend.core.bootstrap import load_env

load_env()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: tests requiring live PostgreSQL (skip if DB unavailable)",
    )
