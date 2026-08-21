# Module 3 - Configure Agents & Environment

⏱️ ~15 min

## Step 1: Configure local `.env`

Run from:

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilot/src/PersonalCareerCopilot
```

Module 2 copied the template to `.env`. Fill in all six values:

```env
FOUNDRY_PROJECT_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project>
AZURE_AI_MODEL_DEPLOYMENT_NAME=<your-model-deployment-name>
CAREERS_MCP_ENDPOINT=https://<trainer-provided-host>/mcp
CAREERS_MCP_API_KEY=<trainer-provided-event-key>
CAREERS_MCP_TIMEOUT_SECONDS=10
MICROSOFT_LEARN_MCP_ENDPOINT=https://learn.microsoft.com/api/mcp
```

- Use the endpoint and model from **your** attendee Foundry project.
- Use the Careers endpoint/key distributed by the trainer out of band. Do not
  substitute trainer project details.
- The trainer-provided Careers endpoint must use HTTPS with no embedded
  credentials, query, or fragment. Plain HTTP is accepted only for loopback
  development endpoints such as `127.0.0.1`.
- Timeout must be greater than 0 and no more than 30 seconds.
- Never commit `.env`, display the key in a screenshot, or paste it into prompts.

`FOUNDRY_PROJECT_ENDPOINT` is the local and Hosted Agent runtime value consumed
by `main.py`. Deployment also requires these distinct `azd` settings:

- `AZURE_AI_PROJECT_ENDPOINT` — project endpoint used by the `azd` Foundry extension.
- `AZURE_AI_PROJECT_ID` — full ARM resource ID of the project.
- `AZURE_SUBSCRIPTION_ID` — attendee subscription.
- `AZURE_LOCATION` — attendee project region.

Module 6 sets those four values plus `FOUNDRY_PROJECT_ENDPOINT` in the `azd`
environment. The two endpoint variables use the same URL but have different
consumers; neither is interchangeable with the ARM project ID.

## Step 2: Install pinned dependencies

Use Python 3.13 locally to match Hosted Agent runtime `python_3_13`:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell activation:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Do not replace exact pins with “latest”. The checked-in versions are:

| Package | Exact version |
|---|---|
| `agent-framework-foundry` | `1.10.4` |
| `agent-framework-foundry-hosting` | `1.0.0b260730` |
| `azure-identity` | `1.25.3` |
| `debugpy` | `1.8.21` |
| `httpx` | `0.28.1` |
| `mcp` | `1.29.0` |
| `opentelemetry-exporter-otlp-proto-grpc` | `1.43.0` |
| `python-dotenv` | `1.2.2` |

Verify the local host, tracing exporter, and runtime packages:

```bash
python -m pip show \
  agent-framework-foundry \
  agent-framework-foundry-hosting \
  mcp \
  opentelemetry-exporter-otlp-proto-grpc \
  debugpy
```

## Step 3: Replace the generated sample agents

Open generated `main.py`. Remove `writer_agent`, `legal_agent`, and
`format_agent`; keep the generated Foundry client and Responses host pattern.

Copy the four prompt constants from
[`lab-assets/base-agent-prompts.md`](../lab-assets/base-agent-prompts.md), then
create these agents:

### `ResumeParser`

- Parses only the supplied synthetic resume.
- Copies any pasted fallback exactly to `[JOB DESCRIPTION PASS-THROUGH]`.

### `JobDescriptionAgent`

- Extracts requirements only from `[JOB DESCRIPTION PASS-THROUGH]`.
- Copies `[PARSED RESUME]` into `[PARSED RESUME PASS-THROUGH]`.
- Does not use candidate evidence as job requirements.

### `MatchingAgent`

- Compares only `[JD REQUIREMENTS]` with `[PARSED RESUME PASS-THROUGH]`.
- Produces evidence-based score math and precise gaps.

### `GapAnalyzer`

- Calls `search_microsoft_learn_for_plan` for every High/Medium gap.
- Marks Microsoft Learn resources unavailable when that MCP call fails; it does
  not present fallback links as live results.

The optional Careers challenge later adds `[SELECTED JOB KEY]`, `[SOURCE JOB]`,
exact-key retrieval, and the deterministic failure branch.

## Step 4: Add the Microsoft Learn tool

Add these imports to generated `main.py`:

```python
import json

import httpx
from agent_framework import tool
from mcp import ClientSession
from mcp.client.streamable_http import StreamableHTTPError, streamable_http_client
from mcp.shared.exceptions import McpError
```

Use
[`lab-assets/microsoft-learn-tool.md`](../lab-assets/microsoft-learn-tool.md)
to add `search_microsoft_learn_for_plan`. It must:

1. Calls `https://learn.microsoft.com/api/mcp`.
2. Invokes `microsoft_docs_search` with the skill/role query.
3. Returns only successful official results.
4. Returns `[MICROSOFT LEARN MCP FAILURE]` for MCP, HTTP, timeout, OS, grouped,
   or JSON failures.
5. Never turns static fallback URLs into apparent live results.

The asset is a focused implementation snippet, not a pre-created `main.py`.

## Step 5: Verify base tool placement

| Tool | Caller | Purpose |
|---|---|---|
| Microsoft Learn `microsoft_docs_search` | `GapAnalyzer` only | Find official resources for roadmap gaps |

The Careers tools are intentionally absent from the original Lab 02 path.

## Step 6: Verify authentication

```bash
az account show --query "{name:name, id:id}" --output table
```

Confirm this is your attendee subscription. Local inference uses your Azure
credential and your configured Foundry project.

### Checkpoint

- [ ] `.env` is beside `main.py` and contains all six non-placeholder values.
- [ ] The endpoint/key came from the trainer out of band and are not committed.
- [ ] The project endpoint/model belong to me, not the trainer.
- [ ] I can distinguish the runtime endpoint, `azd` endpoint, ARM project ID,
      subscription, and location settings.
- [ ] Python 3.13 is active and every runtime, debugging, and OTLP pin is installed.
- [ ] I replaced the three sample slogan agents with four Lab 02 agents.
- [ ] I added only the Microsoft Learn tool to `GapAnalyzer`.
- [ ] I have not copied the completed `main.py`.

---

**Previous:** [02 - Scaffold the Attendee Project](02-scaffold-multi-agent.md) ·
**Next:** [04 - Orchestration & Relays →](04-orchestration-patterns.md)
