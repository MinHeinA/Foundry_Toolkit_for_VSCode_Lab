"""Bounded service operations shared by REST and MCP."""

from __future__ import annotations

import contextvars
import json
import logging
import time
from typing import Any

from .repository import JobRepository, QueryValidationError, RepositoryError

MAX_DETAIL_RESPONSE_BYTES = 49_152
MAX_DETAIL_FIELD_BYTES = 10_000
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "careers_correlation_id",
    default="not-request-scoped",
)


class ServiceError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _clip_utf8(value: str, maximum: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum:
        return value, False
    clipped = encoded[: maximum - 3].decode("utf-8", errors="ignore").rstrip()
    return f"{clipped}...", True


class CareersService:
    def __init__(self, repository: JobRepository, logger: logging.Logger | None = None):
        self.repository = repository
        self.logger = logger or logging.getLogger("careers_job_mcp.operations")

    def _dataset_version(self) -> str:
        try:
            return self.repository.metadata()["dataset_version"]
        except RepositoryError:
            return "unavailable"

    def _log(
        self,
        operation: str,
        status: str,
        started: float,
        result_count: int,
        dataset_version: str,
    ) -> None:
        event = {
            "operation": operation,
            "status": status,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "result_count": result_count,
            "dataset_version": dataset_version,
            "correlation_id": correlation_id_var.get(),
        }
        self.logger.info(json.dumps(event, sort_keys=True, separators=(",", ":")))

    def search_jobs(
        self,
        query: str,
        agency: str | None = None,
        field: str | None = None,
        employment_type: str | None = None,
        max_experience_years: int | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            metadata = self.repository.metadata()
            jobs = self.repository.search(
                query,
                agency=agency,
                field=field,
                employment_type=employment_type,
                max_experience_years=max_experience_years,
                limit=limit,
            )
            result = {"jobs": jobs, "dataset": metadata}
            self._log(
                "search_jobs",
                "ok",
                started,
                len(jobs),
                metadata["dataset_version"],
            )
            return result
        except QueryValidationError as exc:
            self._log("search_jobs", "invalid", started, 0, self._dataset_version())
            raise ServiceError("invalid_request", str(exc), 422) from exc
        except RepositoryError as exc:
            self._log("search_jobs", "unavailable", started, 0, "unavailable")
            raise ServiceError("dataset_unavailable", str(exc), 503) from exc

    def get_job(self, job_key: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            metadata = self.repository.metadata()
            job = self.repository.get(job_key)
            if job is None:
                self._log(
                    "get_job", "not_found", started, 0, metadata["dataset_version"]
                )
                raise ServiceError("job_not_found", "No job exists for that job_key", 404)

            truncated_fields: list[str] = []
            for field in (
                "agency_description",
                "description",
                "responsibilities",
                "requirements",
            ):
                job[field], truncated = _clip_utf8(job[field], MAX_DETAIL_FIELD_BYTES)
                if truncated:
                    truncated_fields.append(field)
            job["content_truncated"] = truncated_fields
            job["provenance"] = {
                "source_repo": metadata["source_repo"],
                "source_commit": metadata["source_commit"],
                "generated_at": metadata["generated_at"],
                "schema_version": metadata["schema_version"],
                "sha256": metadata["sha256"],
            }
            result = {"job": job, "dataset": metadata}
            if len(
                json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ) > MAX_DETAIL_RESPONSE_BYTES:
                raise ServiceError(
                    "response_too_large",
                    "The normalized listing exceeds the response size limit",
                    500,
                )
            self._log("get_job", "ok", started, 1, metadata["dataset_version"])
            return result
        except QueryValidationError as exc:
            self._log("get_job", "invalid", started, 0, self._dataset_version())
            raise ServiceError("invalid_request", str(exc), 422) from exc
        except RepositoryError as exc:
            self._log("get_job", "unavailable", started, 0, "unavailable")
            raise ServiceError("dataset_unavailable", str(exc), 503) from exc

    def get_dataset_status(self) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            metadata = self.repository.metadata()
            result = {"status": "ready", "dataset": metadata}
            self._log(
                "get_dataset_status",
                "ok",
                started,
                metadata["active_record_count"],
                metadata["dataset_version"],
            )
            return result
        except RepositoryError as exc:
            self._log("get_dataset_status", "unavailable", started, 0, "unavailable")
            raise ServiceError("dataset_unavailable", str(exc), 503) from exc

