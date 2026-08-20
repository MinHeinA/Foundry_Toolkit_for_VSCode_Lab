from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

import pytest

import careers_mcp


def _search_payload(count: int = 1) -> dict[str, Any]:
    return {
        "jobs": [
            {
                "job_key": f"hrp:{index}:posting-{index}",
                "title": f"Platform Engineer {index}",
                "agency": "Agency One",
                "field": "Information Technology",
                "employment_type": "Permanent",
                "experience": {
                    "minimum_years": 0,
                    "maximum_years": 5,
                    "label": "00-05 year(s)",
                },
                "closing_date": "2030-01-01",
                "summary": "Build cloud platforms.",
                "source_url": f"https://jobs.example/{index}",
            }
            for index in range(1, count + 1)
        ],
        "dataset": {"dataset_version": "1:source:sha"},
    }


def _job_payload(description: str = "Build platforms.") -> dict[str, Any]:
    return {
        "job": {
            "job_key": "hrp:100:post-a",
            "title": "Platform Engineer",
            "agency": "Agency One",
            "description": description,
            "responsibilities": "Design systems.",
            "requirements": "Python and SQL.",
            "source_url": "https://jobs.example/100",
        },
        "dataset": {"dataset_version": "1:source:sha"},
    }


def _install_fake_mcp(
    monkeypatch: pytest.MonkeyPatch,
    result: Any,
    captured: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    calls: list[tuple[str, dict[str, Any]]] = []

    @asynccontextmanager
    async def fake_streamable_http_client(
        endpoint: str, *, http_client: Any
    ):
        captured["endpoint"] = endpoint
        captured["headers"] = dict(http_client.headers)
        captured["timeout"] = http_client.timeout
        yield object(), object(), None

    class FakeSession:
        def __init__(self, _read: Any, _write: Any) -> None:
            pass

        async def __aenter__(self) -> "FakeSession":
            return self

        async def __aexit__(self, *_args: Any) -> None:
            return None

        async def initialize(self) -> None:
            captured["initialized"] = True

        async def call_tool(
            self, name: str, arguments: dict[str, Any]
        ) -> Any:
            calls.append((name, arguments))
            return result

    monkeypatch.setattr(
        careers_mcp, "streamable_http_client", fake_streamable_http_client
    )
    monkeypatch.setattr(careers_mcp, "ClientSession", FakeSession)
    return calls


def _result(
    structured_content: dict[str, Any] | None,
    *,
    is_error: bool = False,
    error_text: str = "",
) -> Any:
    content = [SimpleNamespace(text=error_text)] if error_text else []
    return SimpleNamespace(
        structuredContent=structured_content,
        isError=is_error,
        content=content,
    )


def test_config_fails_closed_and_hides_key() -> None:
    with pytest.raises(careers_mcp.CareersMcpConfigurationError):
        careers_mcp.CareersMcpConfig.from_env({})
    with pytest.raises(careers_mcp.CareersMcpConfigurationError):
        careers_mcp.CareersMcpConfig.from_env(
            {
                "CAREERS_MCP_ENDPOINT": "https://jobs.example/mcp?key=leak",
                "CAREERS_MCP_API_KEY": "secret",
            }
        )
    with pytest.raises(careers_mcp.CareersMcpConfigurationError):
        careers_mcp.CareersMcpConfig.from_env(
            {
                "CAREERS_MCP_ENDPOINT": "https://jobs.example/mcp",
                "CAREERS_MCP_API_KEY": "<careers-workshop-api-key>",
            }
        )

    config = careers_mcp.CareersMcpConfig.from_env(
        {
            "CAREERS_MCP_ENDPOINT": "https://jobs.example/mcp",
            "CAREERS_MCP_API_KEY": "not-for-repr",
            "CAREERS_MCP_TIMEOUT_SECONDS": "8",
        }
    )
    assert "not-for-repr" not in repr(config)
    assert config.timeout_seconds == 8


def test_search_uses_exact_custom_header_and_parses_structured_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    payload = _search_payload()
    calls = _install_fake_mcp(monkeypatch, _result(payload), captured)
    config = careers_mcp.CareersMcpConfig(
        endpoint="https://jobs.example/mcp",
        api_key="workshop-secret",
        timeout_seconds=7,
    )

    response = asyncio.run(
        careers_mcp.search_jobs(
            "platform engineer",
            max_experience_years=5,
            config=config,
        )
    )

    assert response == payload
    assert captured["endpoint"] == "https://jobs.example/mcp"
    assert captured["headers"]["x-careers-workshop-key"] == "workshop-secret"
    assert "authorization" not in captured["headers"]
    assert captured["initialized"] is True
    assert calls == [
        (
            "search_jobs",
            {
                "query": "platform engineer",
                "max_experience_years": 5,
                "limit": 5,
            },
        )
    ]


def test_get_job_parses_service_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    payload = _job_payload()
    calls = _install_fake_mcp(monkeypatch, _result(payload), captured)

    response = asyncio.run(
        careers_mcp.get_job(
            "hrp:100:post-a",
            config=careers_mcp.CareersMcpConfig(
                endpoint="http://localhost/mcp",
                api_key="test-key",
            ),
        )
    )

    assert response["job"]["title"] == "Platform Engineer"
    assert response["dataset"]["dataset_version"] == "1:source:sha"
    assert calls == [("get_job", {"job_key": "hrp:100:post-a"})]


def test_explicit_tool_error_is_typed_and_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    _install_fake_mcp(
        monkeypatch,
        _result(
            None,
            is_error=True,
            error_text="job_not_found: secret backend details",
        ),
        captured,
    )

    with pytest.raises(careers_mcp.CareersMcpToolError) as error:
        asyncio.run(
            careers_mcp.get_job(
                "hrp:999:missing",
                config=careers_mcp.CareersMcpConfig(
                    endpoint="http://localhost/mcp",
                    api_key="test-key",
                ),
            )
        )

    assert error.value.code == "job_not_found"
    assert "secret backend details" not in str(error.value)


def test_argument_and_structured_payload_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(careers_mcp.CareersMcpValidationError):
        asyncio.run(careers_mcp.search_jobs("x" * 201))
    with pytest.raises(careers_mcp.CareersMcpValidationError):
        asyncio.run(careers_mcp.get_job("not-a-stable-key"))

    captured: dict[str, Any] = {}
    _install_fake_mcp(
        monkeypatch,
        _result(_job_payload("x" * careers_mcp.MAX_STRUCTURED_RESPONSE_BYTES)),
        captured,
    )
    with pytest.raises(careers_mcp.CareersMcpPayloadError):
        asyncio.run(
            careers_mcp.get_job(
                "hrp:100:post-a",
                config=careers_mcp.CareersMcpConfig(
                    endpoint="http://localhost/mcp",
                    api_key="test-key",
                ),
            )
        )


def test_missing_structured_content_is_protocol_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    _install_fake_mcp(monkeypatch, _result(None), captured)
    with pytest.raises(careers_mcp.CareersMcpProtocolError):
        asyncio.run(
            careers_mcp.search_jobs(
                "platform",
                config=careers_mcp.CareersMcpConfig(
                    endpoint="http://localhost/mcp",
                    api_key="test-key",
                ),
            )
        )


def test_transport_failure_is_typed_without_internal_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @asynccontextmanager
    async def failing_transport(_endpoint: str, *, http_client: Any):
        del http_client
        raise careers_mcp.StreamableHTTPError("secret network details")
        yield

    monkeypatch.setattr(
        careers_mcp, "streamable_http_client", failing_transport
    )
    with pytest.raises(careers_mcp.CareersMcpTransportError) as error:
        asyncio.run(
            careers_mcp.search_jobs(
                "platform",
                config=careers_mcp.CareersMcpConfig(
                    endpoint="http://localhost/mcp",
                    api_key="test-key",
                ),
            )
        )
    assert "secret network details" not in str(error.value)


def test_search_cli_prints_at_most_five_compact_cards(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CAREERS_MCP_ENDPOINT", "https://jobs.example/mcp")
    monkeypatch.setenv("CAREERS_MCP_API_KEY", "test-key")
    observed: dict[str, Any] = {}

    async def fake_search_jobs(query: str, **kwargs: Any) -> dict[str, Any]:
        observed["query"] = query
        observed.update(kwargs)
        return _search_payload(6)

    monkeypatch.setattr(careers_mcp, "search_jobs", fake_search_jobs)
    exit_code = careers_mcp.main(
        [
            "search",
            "--query",
            "cloud platform engineer",
            "--max-experience-years",
            "5",
        ]
    )

    output = capsys.readouterr()
    assert exit_code == 0
    assert output.err == ""
    assert output.out.count("    Key: ") == 5
    assert "hrp:5:posting-5" in output.out
    assert "hrp:6:posting-6" not in output.out
    assert observed["query"] == "cloud platform engineer"
    assert observed["max_experience_years"] == 5
