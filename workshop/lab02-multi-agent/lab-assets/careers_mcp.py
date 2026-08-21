"""Bounded client and local CLI for the workshop Careers MCP service."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import StreamableHTTPError, streamable_http_client
from mcp.shared.exceptions import McpError

CAREERS_API_KEY_HEADER = "x-careers-workshop-key"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_TIMEOUT_SECONDS = 30.0
MAX_QUERY_CHARS = 200
MAX_FILTER_CHARS = 200
MAX_JOB_KEY_CHARS = 520
MAX_SEARCH_RESULTS = 5
MAX_STRUCTURED_RESPONSE_BYTES = 65_536
MAX_API_KEY_CHARS = 1_024
_TOOL_ERROR_CODE = re.compile(r"^([a-z][a-z0-9_]{0,63}):")


class CareersMcpError(RuntimeError):
    """Base class for safe, user-facing Careers MCP failures."""


class CareersMcpConfigurationError(CareersMcpError):
    """Raised when required client configuration is absent or unsafe."""


class CareersMcpValidationError(CareersMcpError):
    """Raised before sending an invalid or oversized tool argument."""


class CareersMcpTransportError(CareersMcpError):
    """Raised when the MCP endpoint cannot be reached."""


class CareersMcpProtocolError(CareersMcpError):
    """Raised when the endpoint returns an unexpected MCP response."""


class CareersMcpPayloadError(CareersMcpProtocolError):
    """Raised when structured tool output exceeds the local response bound."""


class CareersMcpToolError(CareersMcpError):
    """Raised when a Careers MCP tool explicitly reports failure."""

    def __init__(self, tool_name: str, code: str = "tool_error") -> None:
        self.tool_name = tool_name
        self.code = code
        super().__init__(f"Careers MCP {tool_name} failed ({code}).")


@dataclass(frozen=True, slots=True)
class CareersMcpConfig:
    """Validated connection settings without an API-key-bearing repr."""

    endpoint: str
    api_key: str = field(repr=False)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> "CareersMcpConfig":
        values = os.environ if environ is None else environ
        endpoint = values.get("CAREERS_MCP_ENDPOINT", "").strip()
        api_key = values.get("CAREERS_MCP_API_KEY", "")
        raw_timeout = values.get(
            "CAREERS_MCP_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)
        ).strip()

        if not endpoint:
            raise CareersMcpConfigurationError("CAREERS_MCP_ENDPOINT is required.")
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or "<" in endpoint
            or ">" in endpoint
        ):
            raise CareersMcpConfigurationError(
                "CAREERS_MCP_ENDPOINT must be an absolute HTTP(S) URL without "
                "credentials, query parameters, or fragments."
            )
        if parsed.scheme == "http" and parsed.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise CareersMcpConfigurationError(
                "CAREERS_MCP_ENDPOINT must use HTTPS unless it targets loopback."
            )
        if not api_key or api_key != api_key.strip():
            raise CareersMcpConfigurationError("CAREERS_MCP_API_KEY is required.")
        if (
            len(api_key) > MAX_API_KEY_CHARS
            or _contains_control(api_key)
            or "<" in api_key
            or ">" in api_key
        ):
            raise CareersMcpConfigurationError("CAREERS_MCP_API_KEY is invalid.")
        try:
            timeout_seconds = float(raw_timeout)
        except ValueError as exc:
            raise CareersMcpConfigurationError(
                "CAREERS_MCP_TIMEOUT_SECONDS must be a number."
            ) from exc
        if not 0 < timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise CareersMcpConfigurationError(
                f"CAREERS_MCP_TIMEOUT_SECONDS must be greater than 0 and at most "
                f"{MAX_TIMEOUT_SECONDS:g}."
            )
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )


def _contains_control(value: str) -> bool:
    return any(unicodedata.category(char).startswith("C") for char in value)


def _bounded_text(
    value: str | None,
    name: str,
    maximum: int,
    *,
    required: bool = False,
) -> str | None:
    if value is None:
        if required:
            raise CareersMcpValidationError(f"{name} is required.")
        return None
    if not isinstance(value, str):
        raise CareersMcpValidationError(f"{name} must be a string.")
    normalized = unicodedata.normalize("NFKC", value).strip()
    if not normalized:
        if required:
            raise CareersMcpValidationError(f"{name} is required.")
        return None
    if len(normalized) > maximum or _contains_control(normalized):
        raise CareersMcpValidationError(
            f"{name} must be at most {maximum} characters and contain no controls."
        )
    return normalized


def _validate_search_arguments(
    query: str,
    agency: str | None,
    field_name: str | None,
    employment_type: str | None,
    max_experience_years: int | None,
    limit: int,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "query": _bounded_text(query, "query", MAX_QUERY_CHARS, required=True),
    }
    for name, value in (
        ("agency", agency),
        ("field", field_name),
        ("employment_type", employment_type),
    ):
        bounded = _bounded_text(value, name, MAX_FILTER_CHARS)
        if bounded is not None:
            arguments[name] = bounded
    if max_experience_years is not None:
        if (
            isinstance(max_experience_years, bool)
            or not isinstance(max_experience_years, int)
            or not 0 <= max_experience_years <= 100
        ):
            raise CareersMcpValidationError(
                "max_experience_years must be an integer from 0 to 100."
            )
        arguments["max_experience_years"] = max_experience_years
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5:
        raise CareersMcpValidationError("limit must be an integer from 1 to 5.")
    arguments["limit"] = limit
    return arguments


def _extract_tool_error_code(result: Any) -> str:
    for content in getattr(result, "content", ()) or ():
        text = getattr(content, "text", "")
        if isinstance(text, str):
            match = _TOOL_ERROR_CODE.match(text)
            if match:
                return match.group(1)
    return "tool_error"


def _parse_structured_content(result: Any, tool_name: str) -> dict[str, Any]:
    if bool(getattr(result, "isError", False)):
        raise CareersMcpToolError(tool_name, _extract_tool_error_code(result))
    content = getattr(result, "structuredContent", None)
    if not isinstance(content, Mapping):
        raise CareersMcpProtocolError(
            f"Careers MCP {tool_name} returned no structured content."
        )
    try:
        encoded = json.dumps(
            content, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CareersMcpProtocolError(
            f"Careers MCP {tool_name} returned invalid structured content."
        ) from exc
    if len(encoded) > MAX_STRUCTURED_RESPONSE_BYTES:
        raise CareersMcpPayloadError(
            f"Careers MCP {tool_name} response exceeded the local payload limit."
        )
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise CareersMcpProtocolError(
            f"Careers MCP {tool_name} returned an invalid response object."
        )
    return decoded


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CareersMcpProtocolError(f"Careers MCP response is missing {name}.")
    return value


def _require_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CareersMcpProtocolError(f"Careers MCP response is missing {name}.")
    return value


def _validate_dataset(payload: dict[str, Any]) -> dict[str, Any]:
    dataset = _require_mapping(payload.get("dataset"), "dataset metadata")
    _require_string(dataset.get("dataset_version"), "dataset version")
    return dataset


async def _call_tool(
    tool_name: str,
    arguments: dict[str, Any],
    config: CareersMcpConfig | None,
) -> dict[str, Any]:
    settings = config or CareersMcpConfig.from_env()
    timeout = httpx.Timeout(settings.timeout_seconds)
    limits = httpx.Limits(max_connections=2, max_keepalive_connections=1)
    try:
        async with httpx.AsyncClient(
            headers={CAREERS_API_KEY_HEADER: settings.api_key},
            timeout=timeout,
            limits=limits,
            follow_redirects=False,
        ) as http_client:
            async with streamable_http_client(
                settings.endpoint,
                http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
    except CareersMcpError:
        raise
    except McpError as exc:
        raise CareersMcpProtocolError(
            "The Careers MCP endpoint rejected the request."
        ) from exc
    except httpx.TimeoutException as exc:
        raise CareersMcpTransportError(
            "The Careers MCP request timed out."
        ) from exc
    except (
        StreamableHTTPError,
        httpx.HTTPError,
        OSError,
        TimeoutError,
        ExceptionGroup,
    ) as exc:
        raise CareersMcpTransportError(
            "The Careers MCP endpoint is unavailable."
        ) from exc
    return _parse_structured_content(result, tool_name)


async def search_jobs(
    query: str,
    *,
    agency: str | None = None,
    field: str | None = None,
    employment_type: str | None = None,
    max_experience_years: int | None = None,
    limit: int = MAX_SEARCH_RESULTS,
    config: CareersMcpConfig | None = None,
) -> dict[str, Any]:
    """Search active listings and parse at most five compact job cards."""
    arguments = _validate_search_arguments(
        query,
        agency,
        field,
        employment_type,
        max_experience_years,
        limit,
    )
    payload = await _call_tool("search_jobs", arguments, config)
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or len(jobs) > MAX_SEARCH_RESULTS:
        raise CareersMcpProtocolError(
            "Careers MCP search_jobs returned an invalid jobs collection."
        )
    for index, job in enumerate(jobs):
        card = _require_mapping(job, f"job card {index + 1}")
        for key in ("job_key", "title", "agency", "source_url"):
            _require_string(card.get(key), f"job card {index + 1} {key}")
    _validate_dataset(payload)
    return payload


async def get_job(
    job_key: str,
    *,
    config: CareersMcpConfig | None = None,
) -> dict[str, Any]:
    """Retrieve one normalized listing by its exact stable key."""
    normalized = _bounded_text(
        job_key, "job_key", MAX_JOB_KEY_CHARS, required=True
    )
    if normalized is None or normalized.count(":") != 2:
        raise CareersMcpValidationError("job_key has an invalid format.")
    payload = await _call_tool("get_job", {"job_key": normalized}, config)
    job = _require_mapping(payload.get("job"), "job")
    for key in ("job_key", "title", "agency", "source_url"):
        _require_string(job.get(key), f"job {key}")
    if job["job_key"] != normalized:
        raise CareersMcpProtocolError(
            "Careers MCP get_job returned a different job key."
        )
    _validate_dataset(payload)
    return payload


async def get_dataset_status(
    *, config: CareersMcpConfig | None = None
) -> dict[str, Any]:
    """Return the trainer dataset readiness and provenance."""
    payload = await _call_tool("get_dataset_status", {}, config)
    if payload.get("status") != "ready":
        raise CareersMcpProtocolError("The Careers MCP dataset is not ready.")
    _validate_dataset(payload)
    return payload


def _experience_label(job: Mapping[str, Any]) -> str:
    experience = job.get("experience")
    if isinstance(experience, Mapping):
        label = experience.get("label")
        if isinstance(label, str) and label.strip():
            return label.strip()
    return "Not specified"


def _print_search_results(payload: Mapping[str, Any]) -> None:
    jobs = payload.get("jobs")
    if not isinstance(jobs, Sequence) or isinstance(jobs, (str, bytes)):
        raise CareersMcpProtocolError("Careers MCP search response is invalid.")
    if not jobs:
        print("No matching jobs found.")
        return
    for index, value in enumerate(jobs[:MAX_SEARCH_RESULTS], start=1):
        if not isinstance(value, Mapping):
            raise CareersMcpProtocolError("Careers MCP job card is invalid.")
        print(f"[{index}] {value['title']} | {value['agency']}")
        print(f"    Key: {value['job_key']}")
        print(f"    Experience: {_experience_label(value)}")
        detail = " | ".join(
            text
            for text in (value.get("employment_type"), value.get("field"))
            if isinstance(text, str) and text.strip()
        )
        if detail:
            print(f"    {detail}")
        print(f"    URL: {value['source_url']}")


def _print_job(payload: Mapping[str, Any]) -> None:
    job = payload["job"]
    dataset = payload["dataset"]
    print(f"{job['title']} | {job['agency']}")
    print(f"Key: {job['job_key']}")
    print(f"URL: {job['source_url']}")
    print(f"Dataset version: {dataset['dataset_version']}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m careers_mcp",
        description="Query the trainer-hosted Careers MCP service.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search active jobs.")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--agency")
    search_parser.add_argument("--field")
    search_parser.add_argument("--employment-type")
    search_parser.add_argument("--max-experience-years", type=int)
    search_parser.add_argument(
        "--limit", type=int, default=MAX_SEARCH_RESULTS, choices=range(1, 6)
    )

    get_parser = subparsers.add_parser("get", help="Show one selected job.")
    get_parser.add_argument("--job-key", required=True)
    subparsers.add_parser("status", help="Check dataset readiness.")
    return parser


async def _run_command(args: argparse.Namespace) -> None:
    config = CareersMcpConfig.from_env()
    if args.command == "search":
        payload = await search_jobs(
            args.query,
            agency=args.agency,
            field=args.field,
            employment_type=args.employment_type,
            max_experience_years=args.max_experience_years,
            limit=args.limit,
            config=config,
        )
        _print_search_results(payload)
    elif args.command == "get":
        _print_job(await get_job(args.job_key, config=config))
    else:
        payload = await get_dataset_status(config=config)
        print(f"Dataset status: {payload['status']}")
        print(f"Dataset version: {payload['dataset']['dataset_version']}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local learner CLI and return a process exit code."""
    load_dotenv()
    args = _build_parser().parse_args(argv)
    try:
        asyncio.run(_run_command(args))
    except CareersMcpError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
