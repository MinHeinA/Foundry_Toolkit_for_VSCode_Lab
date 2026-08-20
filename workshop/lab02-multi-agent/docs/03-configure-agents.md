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

- Use the endpoint and model from **your** Foundry project.
- Use the Careers endpoint/key distributed by the trainer out of band. Do not
  substitute trainer project details.
- The Careers endpoint must be an absolute HTTP(S) URL with no embedded
  credentials, query, or fragment.
- Timeout must be greater than 0 and no more than 30 seconds.
- Never commit `.env`, display the key in a screenshot, or paste it into prompts.

`FOUNDRY_PROJECT_ENDPOINT` is the local/runtime variable. Module 6 sets the
matching `AZURE_AI_PROJECT_ENDPOINT`, `FOUNDRY_PROJECT_ENDPOINT`,
`AZURE_SUBSCRIPTION_ID`, `AZURE_LOCATION`, and ARM `AZURE_AI_PROJECT_ID` in the
`azd` environment.

## Step 2: Install pinned dependencies

Python 3.13 is recommended locally and matches the Hosted Agent
`python_3_13` runtime.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Do not replace the exact pins in `requirements.txt` with “latest”. The current
runtime pins Agent Framework Foundry, Foundry hosting, Azure Identity, `debugpy`,
`httpx`, MCP, and `python-dotenv` to tested versions.

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
- [ ] Python 3.13 environment is active and pinned requirements installed.
- [ ] I can explain which component performs search, `get_job`, and Learn search.
- [ ] I understand that Careers job text is untrusted data.

---

**Previous:** [02 - Inspect the Direct-Code Project](02-scaffold-multi-agent.md) ·
**Next:** [04 - Orchestration & Relays →](04-orchestration-patterns.md)
