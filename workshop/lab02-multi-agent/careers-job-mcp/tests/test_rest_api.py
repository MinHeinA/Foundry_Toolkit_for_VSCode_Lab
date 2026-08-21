from __future__ import annotations

import logging
from pathlib import Path

from fastapi.testclient import TestClient

from careers_job_mcp.app import API_KEY_HEADER, create_app

from conftest import API_KEY


def test_api_key_is_fail_closed_but_health_is_public(
    database_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("CAREERS_MCP_API_KEY", raising=False)
    app = create_app(database_path=database_path)
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503
        assert client.get("/api/v1/dataset/status").status_code == 503
        assert client.post("/mcp", json={}).status_code == 503


def test_wrong_key_is_rejected_and_readiness_is_public(database_path: Path) -> None:
    app = create_app(database_path=database_path, api_key=API_KEY)
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 200
        response = client.get(
            "/api/v1/dataset/status",
            headers={API_KEY_HEADER: "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_rest_search_get_status_and_not_found(database_path: Path) -> None:
    app = create_app(database_path=database_path, api_key=API_KEY)
    headers = {API_KEY_HEADER: API_KEY}
    with TestClient(app) as client:
        search = client.get(
            "/api/v1/jobs/search",
            params={"query": "platform engineer", "agency": "Agency One", "limit": 2},
            headers=headers,
        )
        assert search.status_code == 200
        assert [job["job_key"] for job in search.json()["jobs"]] == [
            "hrp:100:post-a",
            "hrp:101:post-b",
        ]

        job = client.get("/api/v1/jobs/hrp:100:post-a", headers=headers)
        assert job.status_code == 200
        assert job.json()["job"]["description"] == "Build cloud platforms for public services."
        assert job.json()["job"]["provenance"]["source_commit"]

        status = client.get("/api/v1/dataset/status", headers=headers)
        assert status.status_code == 200
        assert status.json()["dataset"]["active_record_count"] == 5

        missing = client.get("/api/v1/jobs/hrp:999:missing", headers=headers)
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "job_not_found"

        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        schema = openapi.json()
        assert schema["components"]["securitySchemes"]["WorkshopApiKey"] == {
            "type": "apiKey",
            "description": (
                "Trainer-issued event key. Enter the raw key value only; do not "
                "prefix it with 'Bearer' and do not place it in the URL."
            ),
            "in": "header",
            "name": API_KEY_HEADER,
        }
        for path, operation in (
            ("/api/v1/jobs/search", "get"),
            ("/api/v1/jobs/{job_key}", "get"),
            ("/api/v1/dataset/status", "get"),
        ):
            assert {"WorkshopApiKey": []} in schema["paths"][path][operation]["security"]


def test_logs_do_not_contain_query_or_secret(
    database_path: Path,
    operation_logger: logging.Logger,
    caplog,
) -> None:
    app = create_app(
        database_path=database_path,
        api_key=API_KEY,
        logger=operation_logger,
    )
    query = "platform-sensitive-query-marker"
    caplog.set_level(logging.INFO, logger=operation_logger.name)
    with TestClient(app) as client:
        client.get(
            "/api/v1/jobs/search",
            params={"query": query},
            headers={API_KEY_HEADER: API_KEY},
        )
        client.get(
            "/api/v1/dataset/status",
            headers={API_KEY_HEADER: "secret-marker-wrong"},
        )

    log_output = "\n".join(record.getMessage() for record in caplog.records)
    assert query not in log_output
    assert API_KEY not in log_output
    assert "secret-marker-wrong" not in log_output
    assert '"operation":"search_jobs"' in log_output
