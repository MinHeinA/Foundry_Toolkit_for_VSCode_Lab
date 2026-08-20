"""FastAPI REST application with the official Streamable HTTP MCP ASGI app."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .mcp_server import create_mcp_server
from .repository import JobRepository, RepositoryError
from .service import CareersService, ServiceError, correlation_id_var

API_KEY_HEADER = "x-careers-workshop-key"
CORRELATION_HEADER = "x-correlation-id"
MAX_REQUEST_BODY_BYTES = 65_536
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10.0
_CORRELATION_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _error_response(
    status_code: int,
    code: str,
    message: str,
    correlation_id: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message},
            "correlation_id": correlation_id,
        },
        headers={CORRELATION_HEADER: correlation_id},
    )


def _correlation_id(request: Request) -> str:
    supplied = request.headers.get(CORRELATION_HEADER, "")
    if _CORRELATION_RE.fullmatch(supplied):
        return supplied
    return str(uuid.uuid4())


def _protected_path(path: str) -> bool:
    return (
        path == "/mcp"
        or path.startswith("/mcp/")
        or path == "/api/v1"
        or path.startswith("/api/v1/")
    )


def _security_log(
    logger: logging.Logger,
    operation: str,
    status: str,
    started: float,
    correlation_id: str,
    dataset_version: str,
) -> None:
    event = {
        "operation": operation,
        "status": status,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "result_count": 0,
        "dataset_version": dataset_version,
        "correlation_id": correlation_id,
    }
    logger.info(json.dumps(event, sort_keys=True, separators=(",", ":")))


def create_app(
    *,
    database_path: str | Path | None = None,
    api_key: str | None = None,
    request_timeout_seconds: float | None = None,
    logger: logging.Logger | None = None,
) -> FastAPI:
    database_path = database_path or os.environ.get(
        "CAREERS_DB_PATH", "data/careers-jobs.sqlite3"
    )
    configured_key = api_key if api_key is not None else os.environ.get("CAREERS_MCP_API_KEY")
    timeout = request_timeout_seconds or float(
        os.environ.get("CAREERS_REQUEST_TIMEOUT_SECONDS", DEFAULT_REQUEST_TIMEOUT_SECONDS)
    )
    if not 0.1 <= timeout <= 60:
        raise ValueError("CAREERS_REQUEST_TIMEOUT_SECONDS must be from 0.1 to 60")

    repository = JobRepository(database_path)
    operation_logger = logger or logging.getLogger("careers_job_mcp.operations")
    service = CareersService(repository, operation_logger)
    mcp_server = create_mcp_server(service)
    mcp_app = mcp_server.streamable_http_app()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with mcp_app.router.lifespan_context(mcp_app):
            yield

    app = FastAPI(
        title="Careers@Gov Jobs API",
        version="1.0.0",
        description=(
            "Read-only active job discovery. This service does not accept resumes or "
            "personal data."
        ),
        lifespan=lifespan,
    )
    app.state.repository = repository
    app.state.service = service
    app.state.api_key_configured = bool(configured_key)

    @app.middleware("http")
    async def safety_middleware(request: Request, call_next: Any):
        started = time.perf_counter()
        correlation_id = _correlation_id(request)
        token = correlation_id_var.set(correlation_id)
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    too_large = int(content_length) > MAX_REQUEST_BODY_BYTES
                except ValueError:
                    too_large = True
                if too_large:
                    _security_log(
                        operation_logger,
                        "request",
                        "too_large",
                        started,
                        correlation_id,
                        "unavailable",
                    )
                    return _error_response(
                        413,
                        "request_too_large",
                        "Request body exceeds the service limit",
                        correlation_id,
                    )

            if _protected_path(request.url.path):
                if not configured_key:
                    _security_log(
                        operation_logger,
                        "authenticate",
                        "not_configured",
                        started,
                        correlation_id,
                        "unavailable",
                    )
                    return _error_response(
                        503,
                        "service_not_configured",
                        "Protected endpoints are not configured",
                        correlation_id,
                    )
                supplied_key = request.headers.get(API_KEY_HEADER, "")
                matches = secrets.compare_digest(
                    hashlib.sha256(supplied_key.encode("utf-8")).digest(),
                    hashlib.sha256(configured_key.encode("utf-8")).digest(),
                )
                if not matches:
                    _security_log(
                        operation_logger,
                        "authenticate",
                        "unauthorized",
                        started,
                        correlation_id,
                        "unavailable",
                    )
                    return _error_response(
                        401,
                        "unauthorized",
                        "A valid workshop API key is required",
                        correlation_id,
                    )

            try:
                async with asyncio.timeout(timeout):
                    response = await call_next(request)
            except TimeoutError:
                _security_log(
                    operation_logger,
                    "request",
                    "timeout",
                    started,
                    correlation_id,
                    "unavailable",
                )
                return _error_response(
                    504,
                    "request_timeout",
                    "The request exceeded the service time limit",
                    correlation_id,
                )
            response.headers[CORRELATION_HEADER] = correlation_id
            return response
        finally:
            correlation_id_var.reset(token)

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
        return _error_response(
            exc.status_code,
            exc.code,
            exc.message,
            correlation_id_var.get(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            422,
            "invalid_request",
            "Request validation failed",
            correlation_id_var.get(),
        )

    @app.get("/healthz", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def root_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    def ready() -> JSONResponse:
        if not configured_key:
            return _error_response(
                503,
                "not_ready",
                "Workshop API key is not configured",
                correlation_id_var.get(),
            )
        try:
            repository.metadata()
        except RepositoryError:
            return _error_response(
                503,
                "not_ready",
                "Dataset is unavailable",
                correlation_id_var.get(),
            )
        return JSONResponse({"status": "ready"})

    @app.get("/api/v1/jobs/search")
    def search_jobs(
        query: Annotated[str, Query(min_length=1, max_length=200)],
        agency: Annotated[str | None, Query(max_length=200)] = None,
        field: Annotated[str | None, Query(max_length=200)] = None,
        employment_type: Annotated[str | None, Query(max_length=200)] = None,
        max_experience_years: Annotated[int | None, Query(ge=0, le=100)] = None,
        limit: Annotated[int, Query(ge=1, le=5)] = 5,
    ) -> dict[str, Any]:
        return service.search_jobs(
            query,
            agency,
            field,
            employment_type,
            max_experience_years,
            limit,
        )

    @app.get("/api/v1/jobs/{job_key:path}")
    def get_job(job_key: str) -> dict[str, Any]:
        return service.get_job(job_key)

    @app.get("/api/v1/dataset/status")
    def dataset_status() -> dict[str, Any]:
        return service.get_dataset_status()

    app.mount("/", mcp_app)
    return app


app = create_app()
