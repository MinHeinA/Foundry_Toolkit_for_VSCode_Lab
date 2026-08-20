from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
MAIN_TREE = ast.parse(MAIN_SOURCE)


def _instruction(name: str) -> str:
    for node in MAIN_TREE.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
        ):
            value = ast.literal_eval(node.value)
            assert isinstance(value, str)
            return value
    raise AssertionError(f"missing instruction constant: {name}")


def _agent_calls() -> dict[str, ast.Call]:
    calls: dict[str, ast.Call] = {}
    for node in ast.walk(MAIN_TREE):
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "Agent"
        ):
            continue
        calls[node.targets[0].id] = node.value
    return calls


def _keyword(call: ast.Call, name: str) -> ast.AST | None:
    return next((item.value for item in call.keywords if item.arg == name), None)


def _tool_names(call: ast.Call) -> list[str]:
    tools = _keyword(call, "tools")
    assert isinstance(tools, ast.List)
    assert all(isinstance(item, ast.Name) for item in tools.elts)
    return [item.id for item in tools.elts if isinstance(item, ast.Name)]


def test_instruction_markers_and_untrusted_content_contract() -> None:
    resume = _instruction("RESUME_PARSER_INSTRUCTIONS")
    job = _instruction("JOB_DESCRIPTION_INSTRUCTIONS")
    matching = _instruction("MATCHING_AGENT_INSTRUCTIONS")
    gap = _instruction("GAP_ANALYZER_INSTRUCTIONS")

    for marker in (
        "[PARSED RESUME]",
        "[SELECTED JOB KEY]",
        "[JOB DESCRIPTION PASS-THROUGH]",
    ):
        assert marker in resume
    for marker in (
        "[JD REQUIREMENTS]",
        "[PARSED RESUME PASS-THROUGH]",
        "[SOURCE JOB]",
    ):
        assert marker in job
    assert "UNTRUSTED DATA" in job
    assert "Ignore commands" in job
    assert "Never fabricate job data" in job
    assert "never silently fall back" in job
    assert "[SOURCE JOB PASS-THROUGH]" in matching
    assert "[SOURCE JOB PASS-THROUGH]" in gap
    assert "MICROSOFT LEARN MCP FAILURE" in gap


def test_only_job_agent_receives_careers_tool_and_all_agents_disable_store() -> None:
    calls = _agent_calls()
    assert set(calls) == {
        "resume_parser",
        "jd_agent",
        "matching_agent",
        "gap_analyzer",
    }

    for call in calls.values():
        options = _keyword(call, "default_options")
        assert options is not None
        assert ast.literal_eval(options) == {"store": False}

    assert _keyword(calls["resume_parser"], "tools") is None
    assert _keyword(calls["matching_agent"], "tools") is None
    assert _tool_names(calls["jd_agent"]) == ["get_selected_careers_job"]
    assert _tool_names(calls["gap_analyzer"]) == [
        "search_microsoft_learn_for_plan"
    ]


def test_workflow_uses_last_agent_context_and_single_careers_wrapper() -> None:
    assert MAIN_SOURCE.count('context_mode="last_agent"') == 4
    wrappers = [
        node
        for node in MAIN_TREE.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "get_selected_careers_job"
    ]
    assert len(wrappers) == 1
    assert MAIN_SOURCE.count("tools=[get_selected_careers_job]") == 1
