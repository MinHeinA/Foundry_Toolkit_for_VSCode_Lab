"""CLI for downloading and indexing the Careers@Gov source snapshot."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from .index_builder import (
    DEFAULT_SOURCE_COMMIT,
    DEFAULT_SOURCE_REPO,
    DatasetValidationError,
    build_index,
    format_timestamp,
)

MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _default_generated_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is not None:
        try:
            return format_timestamp(datetime.fromtimestamp(int(epoch), UTC))
        except (ValueError, OverflowError) as exc:
            raise DatasetValidationError("SOURCE_DATE_EPOCH must be a Unix timestamp") from exc
    return format_timestamp(datetime.now(UTC))


def _download(commit: str, directory: Path) -> Path:
    if not _COMMIT_RE.fullmatch(commit):
        raise DatasetValidationError("download source commit must be a full lowercase Git SHA")
    url = (
        "https://raw.githubusercontent.com/opengovsg/careersgovsg-jobs-data/"
        f"{commit}/data/job-listings.json"
    )
    with tempfile.NamedTemporaryFile(
        dir=directory,
        prefix=".careers-source.",
        suffix=".json",
        delete=False,
    ) as handle:
        path = Path(handle.name)
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "careers-job-mcp-index-builder/1.0"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                declared_size = response.headers.get("Content-Length")
                if declared_size and int(declared_size) > MAX_DOWNLOAD_BYTES:
                    raise DatasetValidationError("upstream dataset exceeds the download size limit")
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise DatasetValidationError(
                            "upstream dataset exceeds the download size limit"
                        )
                    handle.write(chunk)
        except Exception:
            path.unlink(missing_ok=True)
            raise
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, sanitize, and build the Careers@Gov SQLite FTS5 index."
    )
    parser.add_argument("--input", type=Path, help="Local job-listings.json (no network)")
    parser.add_argument("--output", type=Path, default=Path("data/careers-jobs.sqlite3"))
    parser.add_argument("--source-repo", default=DEFAULT_SOURCE_REPO)
    parser.add_argument("--source-commit", default=DEFAULT_SOURCE_COMMIT)
    parser.add_argument(
        "--generated-at",
        help="RFC 3339 build instant; use this or SOURCE_DATE_EPOCH for byte reproducibility",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    generated_at = args.generated_at or _default_generated_at()
    downloaded: Path | None = None
    try:
        source = args.input
        if source is None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            downloaded = _download(args.source_commit, args.output.parent)
            source = downloaded
        result = build_index(
            source,
            args.output,
            source_repo=args.source_repo,
            source_commit=args.source_commit,
            generated_at=generated_at,
        )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (DatasetValidationError, OSError, urllib.error.URLError) as exc:
        print(f"index build failed: {exc}", file=sys.stderr)
        return 2
    finally:
        if downloaded is not None:
            downloaded.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
