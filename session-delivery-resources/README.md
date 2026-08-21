# How to deliver this session

Thanks for delivering this workshop. Run both labs end to end before the event
and treat the shared Careers service as trainer-operated infrastructure.

## File summary

| Resource | Link | Description |
|---|---|---|
| Workshop slide deck | [Workshop Deck](./foundry-toolkit-deck.pptx) | Slides, presenter notes, and embedded demos |
| Workshop documentation | [Repository](https://github.com/microsoft-foundry/Foundry_Toolkit_for_VSCode_Lab) | Source and step-by-step labs |
| Lab 01 | [Single agent](../workshop/lab01-single-agent/README.md) | Existing Foundry Toolkit flow |
| Lab 02 | [Multi-agent](../workshop/lab02-multi-agent/README.md) | Four sequential agents plus optional shared Careers MCP |
| Lab 02 implementation | [PersonalCareerCopilot](../workshop/lab02-multi-agent/PersonalCareerCopilot/) | Direct-code Hosted Agent and learner CLI |
| Trainer deployment runbook | [trainer-deployment README](../workshop/lab02-multi-agent/trainer-deployment/README.md) | Trainer-only provisioning/deployment commands and operational details |

Do not copy secret values from a delivery environment into this guide, slides,
screenshots, or chat. The runbook is the source of truth for trainer deployment;
this guide provides event operations and learner handoff.

## Delivery model

### Lab 01

Lab 01 remains unchanged: scaffold and test with the Foundry extension/Toolkit,
then follow its documented deployment path.

### Lab 02

- Attendees use their own Azure subscription, Foundry project, model, role, and
  quota.
- Attendees do not receive access to trainer project `proj-bravo-1`.
- Attendees do not deploy the shared Careers MCP or run trainer Bicep.
- The trainer pre-deploys one shared, read-only MCP endpoint and distributes
  `CAREERS_MCP_ENDPOINT` plus an event-scoped `CAREERS_MCP_API_KEY` out of band.
- Attendees deploy only the direct-code Hosted Agent with the Lab 02
  `azure.yaml`. They never run `azd provision` or `azd up`.
- Only synthetic resumes are allowed. The shared service never receives resume
  data.

The Lab 02 runtime is one Hosted Agent container with four strict sequential
Agent Framework agents:

```text
ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer
```

Careers search happens before the agent through `python -m careers_mcp search`.
`JobDescriptionAgent` alone calls Careers MCP `get_job`; `GapAnalyzer` calls
Microsoft Learn MCP.

## Timing

### Full delivery (about 2 hours)

| Time | Description |
|---|---|
| 0:00–10:00 | Hosted agents, ownership boundaries, privacy, and preview limits |
| 10:00–20:00 | Demo 1: Executive Agent |
| 20:00–60:00 | Lab 01 |
| 60:00–110:00 | Lab 02: search, explicit selection, local test, direct-code deployment, validation |
| 110:00–120:00 | Wrap-up, cleanup responsibilities, and Q&A |

For a short delivery, run Lab 01 and demonstrate Lab 02 rather than rushing
attendees through cloud deployment.

## Trainer prerequisites

- Azure/Foundry permissions described in the
  [trainer deployment runbook](../workshop/lab02-multi-agent/trainer-deployment/README.md).
- An attendee-independent reference Hosted Agent and model quota for trainer
  canaries.
- Azure CLI, `azd`, VS Code, Foundry Toolkit, and Python 3.13.
- A 32-character-or-longer event key held outside source control.
- A clean attendee machine/repository checkout for rehearsal.
- Synthetic demo resumes and known expected selected-key/source results.

## Governance gate: must pass before deployment

Do not provision the trainer service until all gates are recorded as approved:

- Narrow policy exemption/approved path for the one Container App and, if
  required, one `AcrPull` role assignment.
- Trainer deployment identity has the required resource-group, ACR push, and
  Foundry project permissions.
- Publishing and attributing the derived OpenGovSG snapshot is approved.
- Container Apps environment usage confirms enough headroom for the configured
  maximum replicas.
- No additional services outside the approved trainer plan will be created.

Follow the
[trainer-deployment README](../workshop/lab02-multi-agent/trainer-deployment/README.md)
for exact commands and resource configuration. Do not reproduce keys or trainer
resource identifiers in attendee instructions.

## Predeployment and event runbook

The event is **2026-08-27**.

### Before 2026-08-26

1. Complete the governance gate.
2. Follow the trainer deployment runbook to deploy one shared read-only Careers
   MCP endpoint and the reference Hosted Agent.
3. Verify health/readiness, authenticated MCP `tools/list`, `search_jobs`,
   `get_job`, and dataset status.
4. Verify anonymous/incorrect-key access fails.
5. Run selected-key, prompt-injection, unavailable-MCP, and pasted-JD regression
   evaluations.
6. Load-test the expected event burst and confirm logs contain no query text,
   resume text, job bodies, result payloads, or API keys.

### Freeze on 2026-08-26

- Freeze the approved snapshot, immutable image, and reference agent version no
  later than **2026-08-26**.
- Record the dataset version and known-good selected keys for canaries.
- Keep the previous known-good Container App revision available for rollback.
- Rotate from rehearsal credentials to the event-scoped API key using the
  trainer runbook: provision the secret, restart active Container App revisions,
  redeploy the reference agent, verify the new key succeeds, and verify the old
  key fails.
- Rehearse from a clean learner machine using only published attendee steps.

### Event window on 2026-08-27

1. At least 60 minutes before start, raise the shared service minimum to **two
   warm replicas**.
2. Run health, authenticated search/get, dataset provenance, reference-agent
   selected-key, Microsoft Learn, and pasted-JD canaries.
3. Distribute the endpoint/key out of band only after canaries pass.
4. Make **no service, data, image, agent, or key deployments/changes during the
   event**.
5. If Careers MCP degrades, direct learners to a new request using the pasted
   `Job Description:` fallback. Do not silently switch a failed selected-key
   request.

### After the event

1. Rotate or disable the event key immediately, restart active Container App
   revisions, and redeploy/disable the reference agent so no running workload
   retains the event credential.
2. Return the minimum replica count to the approved post-event setting.
3. Preserve redacted validation evidence and review operational metrics.
4. Do not delete resources without separate destructive-action approval.

## Endpoint/key distribution

Use an approved private event channel. Send only:

```text
CAREERS_MCP_ENDPOINT=<event endpoint ending in /mcp>
CAREERS_MCP_API_KEY=<event-scoped key>
```

Remind attendees to place them in local `.env` and their own `azd` environment,
never source control. Do not include a real endpoint/key in decks, recordings,
QR codes, public chat, tickets, or repository issues. If leakage is suspected,
rotate immediately and redistribute out of band.

## Demo 1: Executive Agent

Use the existing [Lab 01 agent](../workshop/lab01-single-agent/agent/):

1. Show the prompt and single-agent definition.
2. Launch its local Agent Inspector flow.
3. Run the sample executive-summary prompt.
4. Explain Lab 01 deployment artifacts and lifecycle.

## Demo 2: Careers-selected Resume → Job Fit

Use
[`PersonalCareerCopilot`](../workshop/lab02-multi-agent/PersonalCareerCopilot/):

1. Show `.env` placeholders without revealing issued values.
2. Run:

   ```bash
   python -m careers_mcp search \
     --query "cloud platform engineer" \
     --max-experience-years 5
   ```

3. Explicitly choose one displayed `Key:`.
4. In Agent Inspector, submit a synthetic resume plus `Selected Job Key:`.
5. Trace `[SELECTED JOB KEY]`, `[SOURCE JOB]`, and
   `[SOURCE JOB PASS-THROUGH]`.
6. Verify the final exact key, canonical source URL, and dataset version.
7. Explain that retrieved jobs are untrusted data and cannot issue instructions.
8. Run a short pasted `Job Description:` fallback with no selected key.
9. Show the Lab 02 parent `azure.yaml` and explain `azd` direct-code deployment;
   do not show the old `agent.yaml`/Inspector deployment path.

## Learner handoff checklist

- [ ] Learner is using their own subscription and Foundry project.
- [ ] Python 3.13 and pinned requirements are installed.
- [ ] Endpoint/key were received out of band and are not visible on screen.
- [ ] Search is run from `PersonalCareerCopilot`.
- [ ] One exact key is selected; the model does not choose.
- [ ] Agent Inspector input contains only synthetic resume data.
- [ ] Final source URL, key, and dataset version match the selection.
- [ ] Pasted-JD regression passes.
- [ ] Deployment uses only `azd deploy personal-career-copilot --no-prompt`.
- [ ] Learner did not run trainer Bicep, `azd provision`, or `azd up`.

## Troubleshooting during delivery

| Symptom | First action |
|---|---|
| Missing/invalid Careers key | Reissue/check the event key through the private channel; update local and attendee `azd` environments |
| Careers 401/403 | Confirm endpoint/key pairing and whether the event key rotated or expired |
| MCP unavailable/timeout | Check trainer canaries; use pasted-JD fallback while trainer restores service |
| Empty search | Broaden the query/remove filters; never invent a key |
| Invalid/expired selected job key | Search the current frozen snapshot and select a returned key |
| Missing source URL/provenance | Trace `[SOURCE JOB]` and `[SOURCE JOB PASS-THROUGH]`; do not infer values |
| Wrong Foundry project/role | Confirm attendee endpoint and ARM project ID match; fix access in the attendee project |
| Model quota/throttling | Use quota in the attendee's own project; trainer quota is not shared |
| Microsoft Learn MCP failure | Keep gap cards, clearly mark official resources unavailable, and retry later |
| Duplicate/missing workflow output | Restore the three-edge strict sequential graph and labeled relays |

See [Lab 02 troubleshooting](../workshop/lab02-multi-agent/docs/08-troubleshooting.md)
for detailed learner fixes.

## Delivery tips

- Keep Agent Inspector visible for local flow, but state clearly that Lab 02
  deployment uses `azd`, not its Deploy button.
- Use only synthetic identities and resumes in live demos and recordings.
- Never “help” a learner by granting access to trainer `proj-bravo-1`.
- Treat source URL, exact selected key, dataset version, and pasted-JD regression
  as required validation—not optional polish.
- Pair learners for the explicit-selection and provenance checks.

## Additional resources

- [Microsoft Foundry documentation](https://learn.microsoft.com/azure/foundry/)
- [Hosted agents overview](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Hosted Agent direct-code development](https://learn.microsoft.com/azure/foundry/how-to/develop/framework-hosted-agents?pivots=programming-language-python)
- [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/)
- [Lab 02 learner documentation](../workshop/lab02-multi-agent/docs/README.md)

## Contacts

Open an issue on the
[workshop repository](https://github.com/microsoft-foundry/Foundry_Toolkit_for_VSCode_Lab/issues)
without secrets or personal data and tag the maintainer.
