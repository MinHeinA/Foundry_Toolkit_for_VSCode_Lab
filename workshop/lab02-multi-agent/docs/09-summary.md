# Module 9 - Summary & Next Steps

⏱️ ~5 min

## What you built

- One direct-code Hosted Agent container using runtime `python_3_13`.
- Four Agent Framework agents running strictly in sequence:
  `ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer`.
- Out-of-band Careers search through the local CLI.
- One explicit stable-key selection and one exact Careers MCP `get_job` call.
- Source provenance relayed through `[SOURCE JOB]` and
  `[SOURCE JOB PASS-THROUGH]`.
- Microsoft Learn MCP lookup by `GapAnalyzer`.
- The original pasted `Job Description:` fallback.

## Key concepts

| Concept | What you practiced |
|---|---|
| Explicit selection | The learner, not the model, chooses one returned stable key |
| Tool separation | CLI performs `search_jobs`; `JobDescriptionAgent` performs `get_job`; `GapAnalyzer` performs Learn search |
| Sequential orchestration | One start, one output, and three ordered `WorkflowBuilder` edges |
| Labeled relays | Exact selected key, source provenance, resume, and fallback JD survive `context_mode="last_agent"` |
| Untrusted data | Retrieved job content supplies facts but cannot issue instructions |
| Privacy boundary | Synthetic resume goes to the learner's project; Careers MCP receives no resume |
| Direct-code deployment | Attendee `azure.yaml` + `azd deploy personal-career-copilot`, with no attendee infrastructure provisioning |

## Completion checklist

### Local configuration and testing

- [x] Used Python 3.13 and installed pinned requirements.
- [x] Configured all six `.env` values without committing secrets.
- [x] Searched with `python -m careers_mcp search`.
- [x] Explicitly selected one exact returned key.
- [x] Used only a synthetic resume in Agent Inspector.
- [x] Verified final source URL, title, agency, exact key, and dataset version.
- [x] Verified job text could not issue instructions.
- [x] Verified the pasted-JD regression path.

### Attendee deployment

- [x] Targeted my own subscription, Foundry project endpoint, ARM project ID,
  model, and quota.
- [x] Set the seven required `azd` environment values.
- [x] Used `AZURE_DEV_USER_AGENT=microsoft_foundry_skill` inline on every `azd`
  command.
- [x] Ran only `azd deploy personal-career-copilot --no-prompt`.
- [x] Did not run `azd provision`, `azd up`, shared-MCP deployment, or trainer Bicep.
- [x] Verified with `azd ai agent show personal-career-copilot --output table`
      without displaying the full environment-bearing agent definition.
- [x] Invoked the hosted agent with an exact key and synthetic resume.

### Hosted validation

- [x] Exact selected key survived every relay.
- [x] Final analysis is grounded in the selected listing.
- [x] Canonical source URL and dataset provenance are present.
- [x] Learn MCP results are live official links or failure is explicitly marked.
- [x] Pasted-JD hosted regression passed without fabricated metadata.
- [x] The shared Careers service received no resume data.

## Operational boundaries

The trainer owns the shared endpoint, event key, data snapshot, scaling,
canaries, and post-event key rotation. Attendees own only their local
configuration and Hosted Agent in their own Foundry project.

If the Careers MCP is unavailable, start a new request with no selected key and
use the pasted `Job Description:` fallback. Never fabricate a listing or silently
switch away from a failed selected key.

## Continue learning

- [Agent Framework](https://learn.microsoft.com/agent-framework/)
- [Hosted Agent direct-code development](https://learn.microsoft.com/azure/foundry/how-to/develop/framework-hosted-agents?pivots=programming-language-python)
- [Model Context Protocol tools](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol)
- [Foundry evaluations](https://learn.microsoft.com/azure/foundry/evaluations/overview)

---

**Previous:** [08 - Troubleshooting](08-troubleshooting.md) ·
**Home:** [Lab 02 README](../README.md) ·
[Workshop Home](../../../README.md)
