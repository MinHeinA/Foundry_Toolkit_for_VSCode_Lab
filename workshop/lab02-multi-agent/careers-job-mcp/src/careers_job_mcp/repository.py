"""Read-only SQLite repository with safe deterministic FTS queries."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_QUERY_CHARS = 200
MAX_FILTER_CHARS = 200
MAX_JOB_KEY_CHARS = 520
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_METADATA_KEYS = {
    "source_repo",
    "source_commit",
    "generated_at",
    "active_record_count",
    "schema_version",
    "sha256",
}


class RepositoryError(RuntimeError):
    """Raised when the immutable dataset cannot be read safely."""


class QueryValidationError(ValueError):
    """Raised for an invalid search or lookup input."""


def _clean_filter(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueryValidationError(f"{name} must be a string")
    cleaned = unicodedata.normalize("NFKC", value).strip()
    if not cleaned or len(cleaned) > MAX_FILTER_CHARS:
        raise QueryValidationError(f"{name} must be 1-{MAX_FILTER_CHARS} characters")
    if any(unicodedata.category(char).startswith("C") for char in cleaned):
        raise QueryValidationError(f"{name} contains invalid control characters")
    return cleaned


def safe_fts_query(query: str) -> str:
    if not isinstance(query, str):
        raise QueryValidationError("query must be a string")
    normalized = unicodedata.normalize("NFKC", query).strip()
    if not 1 <= len(normalized) <= MAX_QUERY_CHARS:
        raise QueryValidationError(f"query must be 1-{MAX_QUERY_CHARS} characters")
    if any(unicodedata.category(char).startswith("C") for char in normalized):
        raise QueryValidationError("query contains invalid control characters")
    tokens = _TOKEN_RE.findall(normalized.casefold())
    if not tokens:
        raise QueryValidationError("query must contain a searchable word or number")
    tokens = tokens[:20]
    return " AND ".join(f'"{token[:64]}"*' for token in tokens)


def _closing_date(milliseconds: int | None) -> str | None:
    if milliseconds is None:
        return None
    return datetime.fromtimestamp(milliseconds / 1000, UTC).date().isoformat()


def _summary(row: sqlite3.Row, max_bytes: int = 320) -> str:
    source = (
        row["description"]
        or row["responsibilities"]
        or row["requirements"]
        or row["agency_description"]
    )
    compact = " ".join(source.split())
    encoded = compact.encode("utf-8")
    if len(encoded) <= max_bytes:
        return compact
    clipped = encoded[: max_bytes - 3].decode("utf-8", errors="ignore").rsplit(" ", 1)[0]
    return f"{clipped}..."


class JobRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.is_file():
            raise RepositoryError("dataset database is unavailable")
        uri = f"{self.database_path.resolve().as_uri()}?mode=ro&immutable=1"
        try:
            connection = sqlite3.connect(uri, uri=True, timeout=2)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only = ON")
            connection.execute("PRAGMA busy_timeout = 2000")
            return connection
        except sqlite3.Error as exc:
            if "connection" in locals():
                connection.close()
            raise RepositoryError("dataset database is unavailable") from exc

    def metadata(self) -> dict[str, Any]:
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute("SELECT key, value FROM metadata ORDER BY key").fetchall()
                metadata = {row["key"]: row["value"] for row in rows}
                missing = _METADATA_KEYS - metadata.keys()
                if missing:
                    raise RepositoryError("dataset metadata is incomplete")
                count = connection.execute("SELECT count(*) FROM jobs").fetchone()[0]
                expected = int(metadata["active_record_count"])
                if count != expected:
                    raise RepositoryError("dataset record count does not match metadata")
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("dataset database is invalid") from exc
        return {
            "source_repo": metadata["source_repo"],
            "source_commit": metadata["source_commit"],
            "generated_at": metadata["generated_at"],
            "active_record_count": int(metadata["active_record_count"]),
            "schema_version": metadata["schema_version"],
            "sha256": metadata["sha256"],
            "dataset_version": (
                f"{metadata['schema_version']}:{metadata['source_commit'][:12]}:"
                f"{metadata['sha256'][:12]}"
            ),
        }

    def search(
        self,
        query: str,
        *,
        agency: str | None = None,
        field: str | None = None,
        employment_type: str | None = None,
        max_experience_years: int | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        fts_query = safe_fts_query(query)
        agency = _clean_filter(agency, "agency")
        field = _clean_filter(field, "field")
        employment_type = _clean_filter(employment_type, "employment_type")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5:
            raise QueryValidationError("limit must be an integer from 1 to 5")
        if max_experience_years is not None and (
            isinstance(max_experience_years, bool)
            or not isinstance(max_experience_years, int)
            or not 0 <= max_experience_years <= 100
        ):
            raise QueryValidationError(
                "max_experience_years must be an integer from 0 to 100"
            )

        clauses = ["jobs_fts MATCH ?"]
        parameters: list[Any] = [fts_query]
        for column, value in (
            ("j.agency", agency),
            ("j.field", field),
            ("j.employment_type", employment_type),
        ):
            if value is not None:
                clauses.append(f"{column} = ? COLLATE NOCASE")
                parameters.append(value)
        if max_experience_years is not None:
            clauses.append("j.experience_years_min <= ?")
            parameters.append(max_experience_years)
        parameters.append(limit)

        sql = f"""
            SELECT
                j.job_key, j.title, j.agency, j.agency_description, j.field,
                j.employment_type, j.experience_required, j.experience_years_min,
                j.experience_years_max, j.closing_date_ms, j.description,
                j.responsibilities, j.requirements, j.source_url
            FROM jobs_fts
            JOIN jobs AS j ON j.rowid = jobs_fts.rowid
            WHERE {" AND ".join(clauses)}
            ORDER BY bm25(jobs_fts, 10.0, 5.0, 4.0, 2.0, 1.0, 1.0, 1.0),
                     j.job_key
            LIMIT ?
        """
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(sql, parameters).fetchall()
        except sqlite3.Error as exc:
            raise RepositoryError("dataset search failed") from exc

        return [
            {
                "job_key": row["job_key"],
                "title": row["title"],
                "agency": row["agency"],
                "field": row["field"],
                "employment_type": row["employment_type"],
                "experience": {
                    "minimum_years": row["experience_years_min"],
                    "maximum_years": row["experience_years_max"],
                    "label": row["experience_required"],
                },
                "closing_date": _closing_date(row["closing_date_ms"]),
                "summary": _summary(row),
                "source_url": row["source_url"],
            }
            for row in rows
        ]

    def get(self, job_key: str) -> dict[str, Any] | None:
        if not isinstance(job_key, str):
            raise QueryValidationError("job_key must be a string")
        normalized = unicodedata.normalize("NFKC", job_key).strip()
        if (
            not 1 <= len(normalized) <= MAX_JOB_KEY_CHARS
            or normalized.count(":") != 2
            or any(unicodedata.category(char).startswith("C") for char in normalized)
        ):
            raise QueryValidationError("job_key has an invalid format")
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM jobs WHERE job_key = ?",
                    (normalized,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryError("dataset lookup failed") from exc
        if row is None:
            return None
        return {
            "job_key": row["job_key"],
            "platform": row["platform"],
            "job_id": row["job_id"],
            "posting_no": row["posting_no"],
            "title": row["title"],
            "agency": row["agency"],
            "agency_description": row["agency_description"],
            "start_date": datetime.fromtimestamp(
                row["start_date_ms"] / 1000, UTC
            ).isoformat().replace("+00:00", "Z"),
            "closing_date": _closing_date(row["closing_date_ms"]),
            "employment_type": row["employment_type"],
            "work_arrangement": row["work_arrangement"],
            "experience": {
                "minimum_years": row["experience_years_min"],
                "maximum_years": row["experience_years_max"],
                "label": row["experience_required"],
            },
            "field": row["field"],
            "functional_area": row["functional_area"],
            "industry": row["industry"],
            "location": row["location"],
            "description": row["description"],
            "responsibilities": row["responsibilities"],
            "requirements": row["requirements"],
            "source_url": row["source_url"],
        }
