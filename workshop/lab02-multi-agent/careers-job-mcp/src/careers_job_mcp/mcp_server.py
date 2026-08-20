"""Official MCP SDK tools shared with the REST service."""

from __future__ import annotations

from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from .service import CareersService, ServiceError


def create_mcp_server(service: CareersService) -> FastMCP:
    mcp = FastMCP(
        "Careers@Gov Jobs",
        instructions=(
            "Read-only public-sector job discovery. Never send resumes, contact details, "
            "or other personal data to this service."
        ),
        host="0.0.0.0",
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        max_request_body_size=65_536,
    )

    @mcp.tool()
    def search_jobs(
        query: Annotated[str, Field(min_length=1, max_length=200)],
        agency: Annotated[str | None, Field(max_length=200)] = None,
        field: Annotated[str | None, Field(max_length=200)] = None,
        employment_type: Annotated[str | None, Field(max_length=200)] = None,
        max_experience_years: Annotated[int | None, Field(ge=0, le=100)] = None,
        limit: Annotated[int, Field(ge=1, le=5)] = 5,
    ) -> dict[str, Any]:
        """Search active jobs and return at most five compact job cards."""
        try:
            return service.search_jobs(
                query,
                agency,
                field,
                employment_type,
                max_experience_years,
                limit,
            )
        except ServiceError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc

    @mcp.tool()
    def get_job(
        job_key: Annotated[str, Field(min_length=1, max_length=520)],
    ) -> dict[str, Any]:
        """Get one normalized job by the exact stable job key."""
        try:
            return service.get_job(job_key)
        except ServiceError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc

    @mcp.tool()
    def get_dataset_status() -> dict[str, Any]:
        """Return dataset provenance, version, count, and readiness."""
        try:
            return service.get_dataset_status()
        except ServiceError as exc:
            raise ToolError(f"{exc.code}: {exc.message}") from exc

    return mcp

