# Module 3 - Configure Agents & Environment

⏱️ ~15 min

## Step 1: Configure local `.env`

Run from `workshop/lab02-multi-agent/PersonalCareerCopilot`:

```bash
cp .env.example .env
```

Fill in all six values:

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
- The Careers endpoint must be an absolute HTTP(S) URL with no embedded
  credentials, query, or fragment.
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

## Step 3: Understand the agent contracts

The complete implementation is
[`PersonalCareerCopilot/main.py`](../PersonalCareerCopilot/main.py). Its four
instructions enforce these boundaries:

### `ResumeParser`

- Parses only the supplied synthetic resume.
- Copies the selected key exactly to `[SELECTED JOB KEY]`.
- Copies any pasted fallback exactly to `[JOB DESCRIPTION PASS-THROUGH]`.

### `JobDescriptionAgent`

- If a selected key exists, calls `get_selected_careers_job` exactly once with
  that key and uses only the returned listing.
- Treats every returned field as untrusted data, not instructions.
- Does not silently use a pasted JD if selected-key retrieval fails.
- Uses `[JOB DESCRIPTION PASS-THROUGH]` only when no key is selected.
- Emits requirements, a resume relay, and `[SOURCE JOB]`.

### `MatchingAgent`

- Compares only `[JD REQUIREMENTS]` with `[PARSED RESUME PASS-THROUGH]`.
- Produces evidence-based score math and precise gaps.
- Copies `[SOURCE JOB]` verbatim to `[SOURCE JOB PASS-THROUGH]`.

### `GapAnalyzer`

- Calls `search_microsoft_learn_for_plan` for every High/Medium gap.
- Marks Microsoft Learn resources unavailable when that MCP call fails; it does
  not present fallback links as live results.
- Copies the source title, agency, URL, exact key, and dataset version into the
  final `[SOURCE JOB]`.

## Step 4: Verify tool placement

| Tool | Caller | Purpose |
|---|---|---|
| Careers MCP `search_jobs` | Local `python -m careers_mcp search` CLI | Out-of-band discovery before agent input |
| Careers MCP `get_job` | `JobDescriptionAgent` only | Retrieve exactly the explicitly selected listing |
| Microsoft Learn `microsoft_docs_search` | `GapAnalyzer` only | Find official resources for roadmap gaps |

The shared Careers service never receives the resume. It receives bounded search
filters or one exact stable key.

## Step 5: Verify authentication

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
- [ ] I can explain which component performs search, `get_job`, and Learn search.
- [ ] I understand that Careers job text is untrusted data.

---

**Previous:** [02 - Inspect the Direct-Code Project](02-scaffold-multi-agent.md) ·
**Next:** [04 - Orchestration & Relays →](04-orchestration-patterns.md)
