# Lab 02 attendee assets

These files support the attendee-generated `PersonalCareerCopilot/` project.
They are not a pre-created agent workspace.

| File | When to use |
|---|---|
| `azure.attendee.yaml` | Replace the generated manifest after targeting the existing Lab 01 Foundry project |
| `.env.example` | Copy to `src/PersonalCareerCopilot/.env` and replace placeholders locally |
| `.agentignore` | Exclude secrets, environments, tests, and editor files from direct-code upload |
| `requirements.completed.txt` | Pin the completed Lab 02 dependency set |
| `base-agent-prompts.md` | Prompt constants for the original pasted-JD workflow |
| `microsoft-learn-tool.md` | Safe Learn MCP endpoint and tool implementation |
| `careers-main-starter.py` | Beginner Careers challenge starter with two focused TODOs |
| `careers_mcp.py` | Copy during the optional Careers@Gov MCP challenge |
| `careers-failure-gate.md` | Conditional stop executor and exact-key verification for the challenge |

The official workflow scaffold creates `main.py`, requirements, deployment
metadata, and project files. Modules 2–4 guide attendees in converting that
generated workflow into the Resume → Job Fit Evaluator.

The optional Careers challenge replaces the generated `main.py` with
`careers-main-starter.py` after saving a backup outside the deployed source
folder. The starter includes the advanced prompt and failure guardrails but
leaves the helper call and least-privilege tool assignment for the attendee.

Do not copy files from `PersonalCareerCopilotCompleted/` until after attempting
the relevant exercise.
