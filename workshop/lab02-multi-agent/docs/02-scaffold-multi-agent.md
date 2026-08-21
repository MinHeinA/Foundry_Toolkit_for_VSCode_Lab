# Module 2 - Start from the Original Lab 02 Baseline

⏱️ ~5 min

Lab 02 separates the attendee workspace from the completed solution:

```text
lab02-multi-agent/
├── azure.yaml
├── PersonalCareerCopilotStarter/  # attendee working directory
│   ├── .agentignore
│   ├── .env.example
│   ├── .vscode/
│   ├── main.py
│   ├── requirements.txt
│   └── requirements-dev.txt
├── PersonalCareerCopilot/         # completed solution and trainer reference
│   ├── careers_mcp.py
│   ├── eval.yaml
│   ├── main.py
│   └── tests/
├── careers-job-mcp/       # trainer-owned service source; attendees do not deploy it
└── trainer-deployment/    # trainer-only azd/Bicep; attendees never run it
```

> [!NOTE]
> Older workshop scaffolding wizards could generate an `agent.yaml` and
> Dockerfile for container deployment. Those legacy artifacts are not part of
> either checked-in Python directory and are not used in this lab.
> Agent Inspector remains the local test client, not the deployment path.

## Key files

| File | Purpose |
|---|---|
| [`../azure.yaml`](../azure.yaml) | Attendee agent-only `azd` manifest; deploys the completed starter, runtime `python_3_13`, no infrastructure |
| [`../PersonalCareerCopilotStarter/main.py`](../PersonalCareerCopilotStarter/main.py) | Runnable original pasted-JD workflow plus numbered Careers MCP TODOs |
| [`../PersonalCareerCopilotStarter/.env.example`](../PersonalCareerCopilotStarter/.env.example) | Credential-free attendee configuration template |
| [`../PersonalCareerCopilotStarter/.vscode/tasks.json`](../PersonalCareerCopilotStarter/.vscode/tasks.json) | Direct local HTTP host task used by Inspector and F5 debugging |
| [`../PersonalCareerCopilot/careers_mcp.py`](../PersonalCareerCopilot/careers_mcp.py) | Provided bounded MCP helper to copy into the starter during the challenge |
| [`../PersonalCareerCopilot/main.py`](../PersonalCareerCopilot/main.py) | Completed read-only solution for comparison and trainer deployment |

Both directories use the same tested Agent Framework, hosting, identity,
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
- `project: PersonalCareerCopilotStarter`
- `codeConfiguration.runtime: python_3_13`
- `codeConfiguration.entryPoint: main.py`
- `kind: hosted`
- Responses protocol `2.0.0`
- service name `personal-career-copilot`
- the model, Careers endpoint/key/timeout, and Microsoft Learn runtime values
- no infrastructure provider or Bicep path

## Prove the original baseline

Before adding Careers MCP, run the starter with a synthetic resume and pasted
job description. Confirm it returns the original fit report and Microsoft Learn
roadmap.

Then copy the bounded helper:

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilotStarter
cp ../PersonalCareerCopilot/careers_mcp.py .
```

## Inspect the target agent boundary

Use the numbered TODOs in starter `main.py`; consult the solution only after
attempting each task. The completed boundary should have:

1. `get_selected_careers_job` calls the validated client by exact key.
2. Careers output is labeled untrusted data.
3. `JobDescriptionAgent` alone registers the Careers tool.
4. `GapAnalyzer` alone registers the Microsoft Learn tool.
5. All four agents disable response storage.
6. `WorkflowBuilder` has exactly three edges in sequence.
7. `configure_tracing()` and required-environment validation run before the
   Foundry client is created.

### Checkpoint

- [ ] I am editing `PersonalCareerCopilotStarter`, not the solution.
- [ ] The original pasted-JD baseline works before I add Careers MCP.
- [ ] I copied the provided bounded helper into the starter.
- [ ] I found attendee `azure.yaml` at the Lab 02 root.
- [ ] I confirmed the Hosted Agent runtime is `python_3_13`.
- [ ] I confirmed all runtime, debugging, and OTLP requirements are pinned.
- [ ] I understand `PersonalCareerCopilot` is the end-state reference.
- [ ] I understand `careers-job-mcp/` and `trainer-deployment/` are trainer-owned.
- [ ] I will not run `azd provision` or `azd up` for Lab 02.

---

**Previous:** [01 - Understand the Architecture](01-understand-multi-agent.md) ·
**Next:** [03 - Configure Agents & Environment →](03-configure-agents.md)
