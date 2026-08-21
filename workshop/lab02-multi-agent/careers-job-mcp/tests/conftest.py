from __future__ import annotations

import logging
from pathlib import Path

import pytest

from careers_job_mcp.index_builder import build_index

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "jobs.json"
GENERATED_AT = "2026-01-01T00:00:00Z"
API_KEY = "unit-test-workshop-key"


@pytest.fixture()
def database_path(tmp_path: Path) -> Path:
    output = tmp_path / "careers.sqlite3"
    build_index(FIXTURE_PATH, output, generated_at=GENERATED_AT)
    return output


@pytest.fixture()
def operation_logger() -> logging.Logger:
    logger = logging.getLogger("careers_job_mcp.tests.operations")
    logger.setLevel(logging.INFO)
    logger.propagate = True
    return logger
