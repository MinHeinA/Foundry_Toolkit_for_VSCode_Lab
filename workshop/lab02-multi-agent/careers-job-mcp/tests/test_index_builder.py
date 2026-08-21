from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from careers_job_mcp.index_builder import DatasetValidationError, build_index

from conftest import FIXTURE_PATH, GENERATED_AT


def _records() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_build_filters_expired_and_records_checksum(database_path: Path) -> None:
    expected_sha = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
    with sqlite3.connect(database_path) as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        count = connection.execute("SELECT count(*) FROM jobs").fetchone()[0]
        expired = connection.execute(
            "SELECT count(*) FROM jobs WHERE job_key = 'hrp:102:expired'"
        ).fetchone()[0]
        normalized_start = connection.execute(
            "SELECT start_date_ms FROM jobs WHERE job_key = 'greenhouse:4001978201:'"
        ).fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

    assert count == 5
    assert expired == 0
    assert normalized_start == 1735689600000
    assert metadata["active_record_count"] == "5"
    assert metadata["generated_at"] == GENERATED_AT
    assert metadata["sha256"] == expected_sha
    assert integrity == "ok"


def test_build_is_byte_deterministic_for_fixed_inputs(tmp_path: Path) -> None:
    first = tmp_path / "first.sqlite3"
    second = tmp_path / "second.sqlite3"
    build_index(FIXTURE_PATH, first, generated_at=GENERATED_AT)
    build_index(FIXTURE_PATH, second, generated_at=GENERATED_AT)

    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(
        second.read_bytes()
    ).digest()


def test_build_keeps_listing_through_its_closing_date(tmp_path: Path) -> None:
    records = _records()
    records[0]["closingDate"] = 1767225600000
    records[0]["closingDateText"] = "Closing on 01 Jan 2026"
    source = tmp_path / "closing-date.json"
    source.write_text(json.dumps(records), encoding="utf-8")

    same_day = tmp_path / "same-day.sqlite3"
    build_index(
        source,
        same_day,
        generated_at="2026-01-01T23:59:59Z",
    )
    next_day = tmp_path / "next-day.sqlite3"
    build_index(
        source,
        next_day,
        generated_at="2026-01-02T00:00:00Z",
    )

    query = "SELECT count(*) FROM jobs WHERE job_key = 'hrp:100:post-a'"
    with sqlite3.connect(same_day) as connection:
        assert connection.execute(query).fetchone()[0] == 1
    with sqlite3.connect(next_day) as connection:
        assert connection.execute(query).fetchone()[0] == 0


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda records: records[0].pop("jobTitle"), "missing required fields"),
        (lambda records: records.append(dict(records[0])), "duplicate composite job key"),
        (
            lambda records: records[0].update({"experienceYearsMin": 9, "experienceYearsMax": 2}),
            "must not exceed",
        ),
        (lambda records: records[0].update({"postingNo": ""}), "postingNo"),
    ],
)
def test_schema_validation_rejects_invalid_records(
    tmp_path: Path, mutator, expected: str
) -> None:
    records = _records()
    mutator(records)
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(records), encoding="utf-8")

    with pytest.raises(DatasetValidationError, match=expected):
        build_index(source, tmp_path / "invalid.sqlite3", generated_at=GENERATED_AT)


def test_failed_build_does_not_replace_existing_database(tmp_path: Path) -> None:
    output = tmp_path / "careers.sqlite3"
    build_index(FIXTURE_PATH, output, generated_at=GENERATED_AT)
    original = hashlib.sha256(output.read_bytes()).digest()
    source = tmp_path / "invalid.json"
    source.write_text("not json", encoding="utf-8")

    with pytest.raises(DatasetValidationError):
        build_index(source, output, generated_at=GENERATED_AT)

    assert hashlib.sha256(output.read_bytes()).digest() == original
