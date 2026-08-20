from pathlib import Path


def test_container_entrypoint_and_healthcheck_are_declared() -> None:
    root = Path(__file__).parents[1]
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12" in dockerfile
    assert "USER app" in dockerfile
    assert "EXPOSE 8080" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert 'python", "-m", "careers_job_mcp"' in dockerfile


def test_entrypoint_imports() -> None:
    from careers_job_mcp.__main__ import main
    from careers_job_mcp.app import app

    assert callable(main)
    assert app is not None

