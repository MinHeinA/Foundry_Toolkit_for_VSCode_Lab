from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from careers_job_mcp.app import API_KEY_HEADER, create_app

from conftest import API_KEY


def test_all_tools_over_streamable_http(database_path: Path) -> None:
    app = create_app(database_path=database_path, api_key=API_KEY)

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://localhost",
                headers={API_KEY_HEADER: API_KEY},
            ) as http_client:
                async with streamable_http_client(
                    "http://localhost/mcp",
                    http_client=http_client,
                ) as (read_stream, write_stream, _):
                    async with ClientSession(read_stream, write_stream) as session:
                        initialized = await session.initialize()
                        assert initialized.serverInfo.name == "Careers@Gov Jobs"

                        tools = await session.list_tools()
                        assert {tool.name for tool in tools.tools} == {
                            "search_jobs",
                            "get_job",
                            "get_dataset_status",
                        }

                        search = await session.call_tool(
                            "search_jobs",
                            {"query": "platform engineer", "limit": 2},
                        )
                        assert not search.isError
                        assert search.structuredContent["jobs"]

                        job = await session.call_tool(
                            "get_job",
                            {"job_key": "greenhouse:4001978201:"},
                        )
                        assert not job.isError
                        assert (
                            job.structuredContent["job"]["source_url"]
                            == "https://jobs.careers.gov.sg/jobs/greenhouse/"
                            "4001978201?gh_jid=4001978201"
                        )

                        status = await session.call_tool("get_dataset_status", {})
                        assert not status.isError
                        assert status.structuredContent["status"] == "ready"

                        missing = await session.call_tool(
                            "get_job",
                            {"job_key": "hrp:999:missing"},
                        )
                        assert missing.isError
                        assert "job_not_found" in missing.content[0].text

    asyncio.run(exercise())

