"""Container and local-process entry point."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "careers_job_mcp.app:app",
        host=os.environ.get("CAREERS_HOST", "0.0.0.0"),
        port=int(os.environ.get("CAREERS_PORT", "8080")),
        log_level=os.environ.get("CAREERS_LOG_LEVEL", "info").lower(),
        access_log=False,
    )


if __name__ == "__main__":
    main()

