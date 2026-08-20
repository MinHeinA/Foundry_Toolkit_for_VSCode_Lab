# Module 2 - Inspect the Direct-Code Project

⏱️ ~5 min

Lab 02 no longer uses the old Foundry Toolkit scaffold/deploy wizard or a
standalone `agent.yaml`. Work from the checked-in implementation:

```text
lab02-multi-agent/
├── azure.yaml
├── PersonalCareerCopilot/
│   ├── .agentignore
│   ├── .env.example
│   ├── careers_mcp.py
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── tests/
├── careers-job-mcp/       # trainer-owned service source; attendees do not deploy it
└── trainer-deployment/    # trainer-only azd/Bicep; attendees never run it
```

> [!NOTE]
> Screenshots in earlier workshop versions showing **Create New Hosted Agent**,
> selection of `agent.yaml`, or **Deploy** in Agent Inspector are obsolete for
> Lab 02 and cannot be reused. Agent Inspector is still used for local testing.
> Lab 01's wizard-based flow is unchanged.

## Key files

| File | Purpose |
|---|---|
| [`../azure.yaml`](../azure.yaml) | Attendee agent-only `azd` manifest; direct-code Hosted Agent, runtime `python_3_13`, no infrastructure |
| [`../PersonalCareerCopilot/main.py`](../PersonalCareerCopilot/main.py) | Responses host, four agents, strict `WorkflowBuilder` chain, Careers `get_job`, and Microsoft Learn MCP tool |
| [`../PersonalCareerCopilot/careers_mcp.py`](../PersonalCareerCopilot/careers_mcp.py) | Bounded authenticated MCP client and learner search/get/status CLI |
| [`../PersonalCareerCopilot/.env.example`](../PersonalCareerCopilot/.env.example) | Credential-free local configuration template |
| [`../PersonalCareerCopilot/.agentignore`](../PersonalCareerCopilot/.agentignore) | Excludes local-only files from direct-code upload |
| [`../PersonalCareerCopilot/requirements.txt`](../PersonalCareerCopilot/requirements.txt) | Exact tested runtime package pins |

The attendee [`azure.yaml`](../azure.yaml) declares only
`personal-career-copilot`. It contains no `infra` block and cannot provision the
shared MCP service. Its Hosted Agent environment passes the model deployment,
Careers endpoint/key/timeout, and Microsoft Learn endpoint into the direct-code
runtime.

## Inspect the deployment manifest

Confirm the checked-in manifest has:

- `host: azure.ai.agent`
- `project: PersonalCareerCopilot`
- `codeConfiguration.runtime: python_3_13`
- `codeConfiguration.entryPoint: main.py`
- `kind: hosted`
- Responses protocol `2.0.0`
- service name `personal-career-copilot`
- no infrastructure provider or Bicep path

## Inspect the agent boundary

In `main.py`, verify:

1. `get_selected_careers_job` calls the validated client by exact key.
2. Careers output is labeled untrusted data.
3. `JobDescriptionAgent` alone registers the Careers tool.
4. `GapAnalyzer` registers the Microsoft Learn tool.
5. `WorkflowBuilder` has exactly three edges in sequence.

### Checkpoint

- [ ] I am using the checked-in direct-code project, not recreating it with a wizard.
- [ ] I found attendee `azure.yaml` at the Lab 02 root.
- [ ] I confirmed the Hosted Agent runtime is `python_3_13`.
- [ ] I confirmed requirements are pinned.
- [ ] I understand `careers-job-mcp/` and `trainer-deployment/` are trainer-owned.
- [ ] I will not run `azd provision` or `azd up` for Lab 02.

---

**Previous:** [01 - Understand the Architecture](01-understand-multi-agent.md) ·
**Next:** [03 - Configure Agents & Environment →](03-configure-agents.md)
