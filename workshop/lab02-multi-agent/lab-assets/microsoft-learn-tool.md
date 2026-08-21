# Microsoft Learn MCP tool

Add these imports to generated `main.py`:

```python
import json
import os
from urllib.parse import urlsplit

import httpx
from agent_framework import tool
from mcp import ClientSession
from mcp.client.streamable_http import StreamableHTTPError, streamable_http_client
from mcp.shared.exceptions import McpError
```

Validate the endpoint before sending skill/role queries:

```python
def get_mcp_endpoint(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or "<" in value
        or ">" in value
    ):
        raise RuntimeError(f"{name} is not a safe absolute MCP URL.")
    if parsed.scheme == "http" and parsed.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise RuntimeError(f"{name} must use HTTPS unless it targets loopback.")
    return value


MICROSOFT_LEARN_MCP_ENDPOINT = get_mcp_endpoint(
    "MICROSOFT_LEARN_MCP_ENDPOINT",
    "https://learn.microsoft.com/api/mcp",
)
```

Add the bounded tool:

```python
@tool
async def search_microsoft_learn_for_plan(
    skill: str,
    role: str = "",
    max_results: int = 5,
) -> str:
    query = " ".join(
        part for part in [skill, role, "learning path module"] if part
    ).strip() or "job skills learning path"
    failure = (
        "[MICROSOFT LEARN MCP FAILURE]\n"
        "Microsoft Learn resources could not be retrieved for this gap."
    )

    try:
        async with streamable_http_client(MICROSOFT_LEARN_MCP_ENDPOINT) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "microsoft_docs_search",
                    {"query": query},
                )

        if result.isError or not result.content:
            return failure
        payload_text = getattr(result.content[0], "text", "")
        data = json.loads(payload_text) if payload_text else {}
        raw_items = data.get("results") if isinstance(data, dict) else None
        if not isinstance(raw_items, list):
            return failure

        items = raw_items[: max(1, min(max_results, 10))]
        lines = [f"Microsoft Learn resources for '{skill}':"]
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            title = item.get("title") or "Microsoft Learn Resource"
            url = item.get("contentUrl") or item.get("url") or item.get("link") or ""
            lines.append(f"{index}. {title} - {url}".rstrip(" -"))
        return "\n".join(lines) if len(lines) > 1 else failure
    except (
        McpError,
        StreamableHTTPError,
        httpx.HTTPError,
        OSError,
        TimeoutError,
        ExceptionGroup,
        json.JSONDecodeError,
    ):
        return failure
```

Assign this tool only to `GapAnalyzer`.
