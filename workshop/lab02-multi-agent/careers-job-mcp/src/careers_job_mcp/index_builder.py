"""Validated, deterministic Careers@Gov SQLite index builder."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .sanitize import sanitize_html

SCHEMA_VERSION = "1"
DEFAULT_SOURCE_REPO = "https://github.com/opengovsg/careersgovsg-jobs-data"
DEFAULT_SOURCE_COMMIT = "84de3599f6927aa48be6f03c4bbb3c58d3965ba5"
MAX_RECORDS = 10_000
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_RAW_RICH_TEXT_CHARS = 1_000_000
MAX_SIMPLE_TEXT_CHARS = 2_000
MAX_PUBLIC_TEXT_CHARS = 512

REQUIRED_FIELDS = frozenset(
    {
        "platform",
        "postingNo",
        "jobId",
        "jobTitle",
        "agency",
        "agencyId",
        "agencyDescription",
        "startDate",
        "closingDate",
        "closingDateText",
        "remainingDays",
        "employmentType",
        "employmentTypeCode",
        "experienceRequired",
        "experienceYearsMin",
        "experienceYearsMax",
        "field",
        "fieldCode",
        "functionalArea",
        "functionalAreaCode",
        "industry",
        "educationCode",
        "isNew",
        "location",
        "jobDescription",
        "jobResponsibilities",
        "jobRequirements",
        "category",
        "workArrangement",
    }
)
_STRING_FIELDS = REQUIRED_FIELDS - {
    "startDate",
    "closingDate",
    "experienceYearsMin",
    "experienceYearsMax",
    "isNew",
}
_RICH_TEXT_FIELDS = (
    "agencyDescription",
    "jobDescription",
    "jobResponsibilities",
    "jobRequirements",
)
_PUBLIC_TEXT_FIELDS = {
    "jobTitle",
    "agency",
    "employmentType",
    "workArrangement",
    "experienceRequired",
    "field",
    "functionalArea",
    "industry",
    "location",
}
_IDENTIFIER_RE = re.compile(r"^[a-z0-9_-]+$")
_JOB_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class DatasetValidationError(ValueError):
    """Raised when an input dataset violates the documented schema."""


@dataclass(frozen=True)
class NormalizedJob:
    job_key: str
    platform: str
    job_id: str
    posting_no: str
    title: str
    agency: str
    agency_description: str
    start_date_ms: int
    closing_date_ms: int | None
    employment_type: str
    work_arrangement: str
    experience_required: str
    experience_years_min: int
    experience_years_max: int
    field: str
    functional_area: str
    industry: str
    location: str
    description: str
    responsibilities: str
    requirements: str
    source_url: str


def parse_generated_at(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise DatasetValidationError("generated timestamp must be RFC 3339") from exc
    if parsed.tzinfo is None:
        raise DatasetValidationError("generated timestamp must include a timezone")
    return parsed.astimezone(UTC).replace(microsecond=0)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalized_string(value: Any, field: str, index: int) -> str:
    if not isinstance(value, str):
        raise DatasetValidationError(f"record {index}: {field} must be a string")
    if field in _RICH_TEXT_FIELDS and len(value) > MAX_RAW_RICH_TEXT_CHARS:
        raise DatasetValidationError(f"record {index}: {field} exceeds the size limit")
    if field not in _RICH_TEXT_FIELDS and len(value) > MAX_SIMPLE_TEXT_CHARS:
        raise DatasetValidationError(f"record {index}: {field} exceeds the size limit")
    if field in _PUBLIC_TEXT_FIELDS and len(value) > MAX_PUBLIC_TEXT_CHARS:
        raise DatasetValidationError(f"record {index}: {field} exceeds the public size limit")
    normalized = unicodedata.normalize("NFKC", value).strip()
    if field not in _RICH_TEXT_FIELDS and any(
        unicodedata.category(char).startswith("C") for char in normalized
    ):
        raise DatasetValidationError(f"record {index}: {field} contains control characters")
    return normalized


def _timestamp_ms(value: Any, field: str, index: int, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DatasetValidationError(f"record {index}: {field} must be a numeric timestamp")
    numeric = float(value)
    if abs(numeric) < 100_000_000_000:
        numeric *= 1000
    milliseconds = int(round(numeric))
    if milliseconds <= 0:
        raise DatasetValidationError(f"record {index}: {field} must be positive")
    return milliseconds


def _experience_years(value: Any, field: str, index: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DatasetValidationError(f"record {index}: {field} must be an integer")
    if not math.isfinite(value) or int(value) != value or not 0 <= int(value) <= 100:
        raise DatasetValidationError(f"record {index}: {field} must be an integer from 0 to 100")
    return int(value)


def canonical_source_url(platform: str, job_id: str, posting_no: str) -> str:
    safe_platform = quote(platform, safe="")
    safe_job_id = quote(job_id, safe="")
    safe_posting_no = quote(posting_no, safe="")
    if platform == "greenhouse":
        return (
            f"https://jobs.careers.gov.sg/jobs/greenhouse/{safe_job_id}"
            f"?gh_jid={safe_job_id}"
        )
    if platform == "workable":
        return f"https://apply.workable.com/j/{safe_posting_no}"
    return (
        f"https://jobs.careers.gov.sg/jobs/{safe_platform}/{safe_job_id}/"
        f"{safe_posting_no}"
    )


def normalize_record(record: Any, index: int) -> NormalizedJob:
    if not isinstance(record, dict):
        raise DatasetValidationError(f"record {index}: expected an object")
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        raise DatasetValidationError(f"record {index}: missing required fields: {', '.join(missing)}")

    strings = {field: _normalized_string(record[field], field, index) for field in _STRING_FIELDS}
    platform = strings["platform"].casefold()
    job_id = strings["jobId"]
    posting_no = strings["postingNo"]
    if not _IDENTIFIER_RE.fullmatch(platform):
        raise DatasetValidationError(f"record {index}: platform has an invalid format")
    if not _JOB_IDENTIFIER_RE.fullmatch(job_id) or len(job_id) > 256:
        raise DatasetValidationError(f"record {index}: jobId has an invalid format")
    if (
        (not posting_no and platform != "greenhouse")
        or (posting_no and not _JOB_IDENTIFIER_RE.fullmatch(posting_no))
        or len(posting_no) > 256
    ):
        raise DatasetValidationError(f"record {index}: postingNo has an invalid format")
    if not strings["jobTitle"]:
        raise DatasetValidationError(f"record {index}: jobTitle must not be empty")
    if not strings["agency"]:
        raise DatasetValidationError(f"record {index}: agency must not be empty")
    if not isinstance(record["isNew"], bool):
        raise DatasetValidationError(f"record {index}: isNew must be a boolean")

    start_date_ms = _timestamp_ms(record["startDate"], "startDate", index)
    closing_date_ms = _timestamp_ms(record["closingDate"], "closingDate", index, nullable=True)
    experience_min = _experience_years(record["experienceYearsMin"], "experienceYearsMin", index)
    experience_max = _experience_years(record["experienceYearsMax"], "experienceYearsMax", index)
    if experience_min > experience_max:
        raise DatasetValidationError(
            f"record {index}: experienceYearsMin must not exceed experienceYearsMax"
        )

    return NormalizedJob(
        job_key=f"{platform}:{job_id}:{posting_no}",
        platform=platform,
        job_id=job_id,
        posting_no=posting_no,
        title=strings["jobTitle"],
        agency=strings["agency"],
        agency_description=sanitize_html(strings["agencyDescription"]),
        start_date_ms=start_date_ms,
        closing_date_ms=closing_date_ms,
        employment_type=strings["employmentType"],
        work_arrangement=strings["workArrangement"],
        experience_required=strings["experienceRequired"],
        experience_years_min=experience_min,
        experience_years_max=experience_max,
        field=strings["field"],
        functional_area=strings["functionalArea"],
        industry=strings["industry"],
        location=strings["location"],
        description=sanitize_html(strings["jobDescription"]),
        responsibilities=sanitize_html(strings["jobResponsibilities"]),
        requirements=sanitize_html(strings["jobRequirements"]),
        source_url=canonical_source_url(platform, job_id, posting_no),
    )


def load_and_normalize(source_bytes: bytes, generated_at: datetime) -> list[NormalizedJob]:
    try:
        payload = json.loads(source_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DatasetValidationError("input is not valid UTF-8 JSON") from exc
    if not isinstance(payload, list):
        raise DatasetValidationError("dataset root must be a JSON array")
    if len(payload) > MAX_RECORDS:
        raise DatasetValidationError(f"dataset exceeds the {MAX_RECORDS} record limit")

    generated_date = generated_at.astimezone(UTC).date()
    jobs: list[NormalizedJob] = []
    seen: set[str] = set()
    for index, record in enumerate(payload):
        job = normalize_record(record, index)
        if job.job_key in seen:
            raise DatasetValidationError(f"record {index}: duplicate composite job key")
        seen.add(job.job_key)
        closing_date = (
            None
            if job.closing_date_ms is None
            else datetime.fromtimestamp(job.closing_date_ms / 1000, UTC).date()
        )
        if closing_date is None or closing_date >= generated_date:
            jobs.append(job)
    return sorted(jobs, key=lambda item: item.job_key)


def _job_values(job: NormalizedJob) -> tuple[Any, ...]:
    return (
        job.job_key,
        job.platform,
        job.job_id,
        job.posting_no,
        job.title,
        job.agency,
        job.agency_description,
        job.start_date_ms,
        job.closing_date_ms,
        job.employment_type,
        job.work_arrangement,
        job.experience_required,
        job.experience_years_min,
        job.experience_years_max,
        job.field,
        job.functional_area,
        job.industry,
        job.location,
        job.description,
        job.responsibilities,
        job.requirements,
        job.source_url,
    )


def build_index(
    input_path: str | Path,
    output_path: str | Path,
    *,
    source_repo: str = DEFAULT_SOURCE_REPO,
    source_commit: str = DEFAULT_SOURCE_COMMIT,
    generated_at: str | datetime,
) -> dict[str, Any]:
    input_file = Path(input_path)
    output_file = Path(output_path)
    if (
        not isinstance(source_repo, str)
        or not 1 <= len(source_repo) <= 500
        or any(unicodedata.category(char).startswith("C") for char in source_repo)
    ):
        raise DatasetValidationError("source repository metadata is invalid")
    if (
        not isinstance(source_commit, str)
        or not 1 <= len(source_commit) <= 128
        or any(unicodedata.category(char).startswith("C") for char in source_commit)
    ):
        raise DatasetValidationError("source commit metadata is invalid")
    if input_file.stat().st_size > MAX_SOURCE_BYTES:
        raise DatasetValidationError("input dataset exceeds the source size limit")
    source_bytes = input_file.read_bytes()
    generated = parse_generated_at(generated_at)
    jobs = load_and_normalize(source_bytes, generated)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    metadata = {
        "active_record_count": str(len(jobs)),
        "generated_at": format_timestamp(generated),
        "schema_version": SCHEMA_VERSION,
        "sha256": source_sha256,
        "source_commit": source_commit,
        "source_repo": source_repo,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output_file.parent,
            prefix=f".{output_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)

        connection = sqlite3.connect(temporary)
        try:
            schema = files("careers_job_mcp").joinpath("schema.sql").read_text(encoding="utf-8")
            connection.executescript(schema)
            connection.executemany(
                """
                INSERT INTO jobs (
                    job_key, platform, job_id, posting_no, title, agency,
                    agency_description, start_date_ms, closing_date_ms,
                    employment_type, work_arrangement, experience_required,
                    experience_years_min, experience_years_max, field,
                    functional_area, industry, location, description,
                    responsibilities, requirements, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (_job_values(job) for job in jobs),
            )
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                sorted(metadata.items()),
            )
            connection.execute("INSERT INTO jobs_fts(jobs_fts) VALUES ('rebuild')")
            connection.execute("INSERT INTO jobs_fts(jobs_fts) VALUES ('optimize')")
            connection.commit()
            connection.execute("VACUUM")
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("SQLite integrity check failed")
            connection.execute(
                "INSERT INTO jobs_fts(jobs_fts, rank) VALUES ('integrity-check', 1)"
            )
            connection.commit()
        finally:
            connection.close()

        os.chmod(temporary, 0o644)
        os.replace(temporary, output_file)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    return {
        "output": str(output_file),
        "active_record_count": len(jobs),
        "generated_at": metadata["generated_at"],
        "sha256": source_sha256,
        "schema_version": SCHEMA_VERSION,
    }
