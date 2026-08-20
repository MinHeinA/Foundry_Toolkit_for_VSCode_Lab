from __future__ import annotations

from pathlib import Path

import pytest

from careers_job_mcp.repository import JobRepository, QueryValidationError


def test_search_is_deterministic_and_filterable(database_path: Path) -> None:
    repository = JobRepository(database_path)

    result = repository.search("platform engineer", agency="agency one", limit=5)
    keys = [job["job_key"] for job in result]
    assert keys == ["hrp:100:post-a", "hrp:101:post-b"]

    assert len(repository.search("platform", limit=1)) == 1
    junior = repository.search("platform", max_experience_years=3, limit=5)
    assert [job["job_key"] for job in junior] == [
        "hrp:100:post-a",
        "hrp:101:post-b",
    ]
    assert repository.search("platform", employment_type="no such type") == []


def test_search_does_not_accept_sql_or_fts_syntax(database_path: Path) -> None:
    repository = JobRepository(database_path)

    assert repository.search('" OR 1=1 --', limit=5) == []
    assert repository.search(
        "platform",
        agency="Agency One' OR 1=1 --",
        limit=5,
    ) == []
    with pytest.raises(QueryValidationError):
        repository.search('"*()--')

    assert repository.metadata()["active_record_count"] == 5


def test_canonical_urls_for_supported_platforms(database_path: Path) -> None:
    repository = JobRepository(database_path)

    assert (
        repository.get("hrp:100:post-a")["source_url"]
        == "https://jobs.careers.gov.sg/jobs/hrp/100/post-a"
    )
    assert (
        repository.get("greenhouse:4001978201:")["source_url"]
        == "https://jobs.careers.gov.sg/jobs/greenhouse/4001978201?gh_jid=4001978201"
    )
    assert (
        repository.get("workable:psd-sg:69C959EF15")["source_url"]
        == "https://apply.workable.com/j/69C959EF15"
    )


def test_get_requires_exact_safe_key(database_path: Path) -> None:
    repository = JobRepository(database_path)
    assert repository.get("hrp:does-not-exist:key") is None
    with pytest.raises(QueryValidationError):
        repository.get("hrp:100:post-a' OR 1=1 --:extra")

