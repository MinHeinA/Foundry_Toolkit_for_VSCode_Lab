# Careers@Gov MCP + REST

Trainer-hosted, read-only job discovery for the multi-agent workshop. It exposes
three MCP tools and matching REST operations over a sanitized, immutable SQLite
FTS5 snapshot. It never accepts resumes or other personal data.

The default source is
[`opengovsg/careersgovsg-jobs-data`](https://github.com/opengovsg/careersgovsg-jobs-data)
at commit `84de3599f6927aa48be6f03c4bbb3c58d3965ba5`. The upstream dataset is
MIT-licensed (see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)) and is not
committed here.

## Set up and build the index

Python 3.12 and SQLite with FTS5 are required.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# Reproducible local-input build (no network)
PYTHONPATH=src .venv/bin/python -m careers_job_mcp.build_index \
  --input /path/to/job-listings.json \
  --source-commit 84de3599f6927aa48be6f03c4bbb3c58d3965ba5 \
  --generated-at 2026-08-20T00:00:00Z \
  --output data/careers-jobs.sqlite3

# Or download the specified upstream commit
PYTHONPATH=src .venv/bin/python -m careers_job_mcp.build_index \
  --source-commit 84de3599f6927aa48be6f03c4bbb3c58d3965ba5 \
  --output data/careers-jobs.sqlite3
```

`--generated-at` (or `SOURCE_DATE_EPOCH`) fixes expiry evaluation and makes
identical inputs byte-reproducible. The stored SHA-256 is the exact source JSON
checksum.

## Run and test

```bash
export CAREERS_MCP_API_KEY='use-a-long-random-shared-key'
export CAREERS_DB_PATH='data/careers-jobs.sqlite3'
PYTHONPATH=src .venv/bin/python -m careers_job_mcp

.venv/bin/pytest
```

The service listens on `CAREERS_HOST`/`CAREERS_PORT` (defaults `0.0.0.0:8080`).
Set `CAREERS_LOG_LEVEL` and `CAREERS_REQUEST_TIMEOUT_SECONDS` as needed. Access
logs are disabled so query strings and keys are never logged.

## Operations

Protected endpoints require `x-careers-workshop-key`.

| MCP tool | REST |
|---|---|
| `search_jobs` | `GET /api/v1/jobs/search?query=platform&limit=5` |
| `get_job` | `GET /api/v1/jobs/{job_key}` |
| `get_dataset_status` | `GET /api/v1/dataset/status` |

MCP Streamable HTTP is at `/mcp`. REST OpenAPI is at `/docs` and
`/openapi.json`. `/healthz` and `/readyz` intentionally require no key.

### Use Swagger UI

1. Open `/docs`.
2. Select **Authorize**.
3. Under `WorkshopApiKey`, paste the raw trainer-issued key only.
4. Select **Authorize**, then **Close**.
5. Open an operation, select **Try it out**, fill its parameters, and execute.

Swagger sends the value in the `x-careers-workshop-key` header. Never put the
key in a URL or query parameter, and do not prefix it with `Bearer`.

```bash
curl -H "x-careers-workshop-key: $CAREERS_MCP_API_KEY" \
  'http://localhost:8080/api/v1/jobs/search?query=data%20engineer&limit=3'

curl -H "x-careers-workshop-key: $CAREERS_MCP_API_KEY" \
  'http://localhost:8080/api/v1/dataset/status'
```

Configure MCP clients with URL `http://localhost:8080/mcp` and the same custom
header. The service uses stateless JSON Streamable HTTP, so a single endpoint is
safe to share across workshop attendees.

## Container

Build the index before the image so it is copied into `/app/data`.

```bash
docker build --platform linux/amd64 -t careers-job-mcp .
docker run --rm -p 8080:8080 \
  -e CAREERS_MCP_API_KEY="$CAREERS_MCP_API_KEY" careers-job-mcp
```

On a restricted network, pre-download Linux CPython 3.12 wheels into
`.wheelhouse/`; the directory contents are git-ignored and the Dockerfile uses
them when present. With only the tracked `.gitkeep`, the normal build downloads
the pinned requirements from PyPI.

The image runs as UID/GID `10001`, exposes port 8080, and has a liveness
healthcheck. No Azure infrastructure is included.
