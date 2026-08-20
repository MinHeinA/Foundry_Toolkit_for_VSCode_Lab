# Module 2 - Inspect the Direct-Code Project

⏱️ ~5 min

Lab 02 uses the checked-in direct-code reference implementation:

```text
lab02-multi-agent/
├── azure.yaml
├── PersonalCareerCopilot/
│   ├── .agentignore
│   ├── .env.example
│   ├── .vscode/
│   ├── careers_mcp.py
│   ├── eval.yaml
│   ├── eval.coverage.yaml
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── tests/
├── careers-job-mcp/       # trainer-owned service source; attendees do not deploy it
└── trainer-deployment/    # trainer-only azd/Bicep; attendees never run it
```

> [!NOTE]
> Older workshop scaffolding wizards could generate an `agent.yaml` and
> Dockerfile for container deployment. Those legacy artifacts are not part of
> the checked-in `PersonalCareerCopilot` reference and are not used in this lab.
> Agent Inspector remains the local test client, not the deployment path.

## Key files

| File | Purpose |
|---|---|
| [`../azure.yaml`](../azure.yaml) | Attendee agent-only `azd` manifest; direct-code Hosted Agent, runtime `python_3_13`, no infrastructure |
| [`../PersonalCareerCopilot/main.py`](../PersonalCareerCopilot/main.py) | Responses host, four agents, strict `WorkflowBuilder` chain, Careers `get_job`, and Microsoft Learn MCP tool |
| [`../PersonalCareerCopilot/careers_mcp.py`](../PersonalCareerCopilot/careers_mcp.py) | Bounded authenticated MCP client and learner search/get/status CLI |
| [`../PersonalCareerCopilot/.env.example`](../PersonalCareerCopilot/.env.example) | Credential-free local configuration template |
| [`../PersonalCareerCopilot/.vscode/tasks.json`](../PersonalCareerCopilot/.vscode/tasks.json) | Direct local HTTP host task used by Inspector and F5 debugging |
| [`../PersonalCareerCopilot/.agentignore`](../PersonalCareerCopilot/.agentignore) | Excludes local-only files from direct-code upload |
| [`../PersonalCareerCopilot/requirements.txt`](../PersonalCareerCopilot/requirements.txt) | Exact runtime, debugging, and OTLP package pins |

The runtime requirements keep the tested Agent Framework, hosting, identity,
HTTP, MCP, and dotenv pins, with exact debugging and tracing pins:

- `debugpy==1.8.21` for direct local breakpoint attach.
- `opentelemetry-exporter-otlp-proto-grpc==1.43.0` for reproducible, optional
  OTLP trace export.

`requirements-dev.txt` layers the pinned pytest dependency on the same runtime
requirements.

## Inspect the deployment manifest

The attendee [`azure.yaml`](../azure.yaml) declares only
`personal-career-copilot`. It contains no `infra` block and cannot provision the
shared MCP service. Confirm it has:

- `host: azure.ai.agent`
- `project: PersonalCareerCopilot`
- `codeConfiguration.runtime: python_3_13`
- `codeConfiguration.entryPoint: main.py`
- `kind: hosted`
- Responses protocol `2.0.0`
- service name `personal-career-copilot`
- the model, Careers endpoint/key/timeout, and Microsoft Learn runtime values
- no infrastructure provider or Bicep path

## Inspect the agent boundary

In `main.py`, verify:

1. `get_selected_careers_job` calls the validated client by exact key.
2. Careers output is labeled untrusted data.
3. `JobDescriptionAgent` alone registers the Careers tool.
4. `GapAnalyzer` alone registers the Microsoft Learn tool.
5. All four agents disable response storage.
6. `WorkflowBuilder` has exactly three edges in sequence.
7. `configure_tracing()` and required-environment validation run before the
   Foundry client is created.

### Checkpoint

- [ ] I am using the checked-in direct-code project, not recreating it with a wizard.
- [ ] I found attendee `azure.yaml` at the Lab 02 root.
- [ ] I confirmed the Hosted Agent runtime is `python_3_13`.
- [ ] I confirmed all runtime, debugging, and OTLP requirements are pinned.
- [ ] I understand `careers-job-mcp/` and `trainer-deployment/` are trainer-owned.
- [ ] I will not run `azd provision` or `azd up` for Lab 02.

---

**Previous:** [01 - Understand the Architecture](01-understand-multi-agent.md) ·
**Next:** [03 - Configure Agents & Environment →](03-configure-agents.md)
