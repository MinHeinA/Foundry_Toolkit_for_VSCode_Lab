# Module 8 - Troubleshooting

Use this guide for the local agent host, Careers MCP integration, and
direct-code `azd` deployment. Never post the event key, `.env`, tokens, or real
resume data in an issue.

## Local agent host startup and configuration

### `RuntimeError` reports a missing or placeholder environment value

`main.py` calls `get_required_environment_variable()` before creating the
Foundry client. It rejects missing values and scaffold placeholders.

1. Confirm `.env` is in `PersonalCareerCopilot/`, beside `main.py`.
2. Copy `.env.example` to `.env`.
3. Replace every placeholder, especially:

   ```env
   FOUNDRY_PROJECT_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project>
   AZURE_AI_MODEL_DEPLOYMENT_NAME=<your-model-deployment-name>
   ```

4. Use the endpoint and model from your own attendee project.
5. Restart the local agent host after editing `.env`.

Because `load_dotenv(override=True)` is used, local `.env` values override values
with the same names in the launching shell. The deployed source does not include
`.env`; Hosted Agent runtime settings are used there.

### Local agent host does not start

Use Python 3.13 and an activated environment:

```bash
python --version
python main.py
```

For breakpoint attach from the command line, run:

```bash
python -m debugpy --listen 127.0.0.1:5679 main.py --port 8088
```

Or run the VS Code task **Run Agent HTTP Server**. For breakpoints, select
**Debug Local Agent HTTP Server**; the task hosts the direct local server on port
8088 and attaches `debugpy` on port 5679.

If startup hangs or a port is occupied:

- Stop any earlier Lab 02 task/process before starting another.
- Confirm both 8088 and 5679 are available.
- Run **Validate prerequisites** from `.vscode/tasks.json`.
- Reopen `PersonalCareerCopilot` as the VS Code workspace so `${workspaceFolder}`
  and `.venv` resolve correctly.

### Agent Inspector or Workflow Visualizer does not connect

- Wait for the local host to report that the application started.
- Open Inspector only after the host is ready.
- Confirm Inspector targets port 8088.
- If only the visualizer port is occupied, change **Hosted Agents: Visualizer
  Port** in Foundry Toolkit settings.
- Restart the local HTTP server task after any port or environment change.

### Local traces are missing

`configure_tracing()` is a privacy-safe optional OTLP helper:
message-content capture remains off by default. If `AGENTDEV_ENABLED=1` is
explicitly set, the helper supplies `http://localhost:4317` and the `grpc`
protocol only when no OTLP endpoint was already configured. That compatibility
branch remains in `main.py`, but Agent Dev is not installed and the documented
direct local-host flow does not require or instruct you to set this variable.

Check:

```bash
python -m pip show opentelemetry-exporter-otlp-proto-grpc
```

Do not enable message-content capture with real personal data.

## Runtime and package issues

Use Python 3.13 locally; direct-code hosting uses `python_3_13`. Install
`requirements.txt` as-is rather than upgrading individual packages:

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

Verify the packages used for hosting, debugging, MCP, and traces:

```bash
python -m pip show \
  agent-framework-foundry \
  agent-framework-foundry-hosting \
  mcp \
  opentelemetry-exporter-otlp-proto-grpc \
  debugpy
```

For `ModuleNotFoundError`, `ImportError`, or a missing `WorkflowBuilder`, recreate
the Python 3.13 virtual environment and reinstall the two checked-in requirement
files. Do not replace exact pins with broad ranges.

## Careers MCP configuration and authentication

### `CAREERS_MCP_ENDPOINT is required` or `CAREERS_MCP_API_KEY is required`

- Confirm `.env` is beside `main.py`.
- Copy from `.env.example` and replace every placeholder.
- Confirm the key has no surrounding whitespace.
- Restart the CLI/server after changing `.env`.

### `CAREERS_MCP_API_KEY is invalid`

The local client rejects empty, placeholder-like, oversized, or unsafe values.
Copy the event key again from the trainer's out-of-band channel. Do not add
quotes to the value inside `.env`.

### HTTP 401/403 from Careers MCP

The event key is missing, wrong, rotated, or expired.

1. Confirm the endpoint and key belong to the same event deployment.
2. Request the current event-scoped key from the trainer out of band.
3. Update both local `.env` and the attendee `azd` environment.
4. Rerun the search CLI, then redeploy the Hosted Agent if its key changed.

Do not ask for access to the trainer Foundry project; it is unrelated to MCP
API-key authentication.

### Endpoint unavailable or request timed out

- Confirm `CAREERS_MCP_ENDPOINT` is the trainer-provided HTTPS `/mcp` URL with no
  query string or fragment.
- Confirm `CAREERS_MCP_TIMEOUT_SECONDS` is numeric, greater than 0, and at most 30.
- Retry once. If multiple attendees fail, notify the trainer; do not deploy the
  service yourself.
- Use the pasted `Job Description:` path in a new request with no selected key.

When a selected key is present and retrieval fails, the agent intentionally does
not silently switch to pasted JD content.

## Search, key, and source issues

### `No matching jobs found`

An empty search is valid. Broaden `--query`, remove optional filters, or increase
`--max-experience-years` if appropriate. Never invent a key. The service returns
at most five cards.

### `job_key has an invalid format`

Copy the complete `Key:` from CLI output. A stable key has exactly three
colon-separated components. Do not change case, punctuation, or whitespace.

### Selected key is no longer found

The key may be absent from the trainer's frozen event snapshot, truncated, or
from an older snapshot. Run the CLI against the current endpoint, select a
returned key, and resubmit. Do not substitute a similar listing.

### Agent retrieves the wrong listing

Compare these values character for character:

1. CLI `Key:` output.
2. Agent Inspector `Selected Job Key:`.
3. `ResumeParser` `[SELECTED JOB KEY]`.
4. `JobDescriptionAgent` `[SOURCE JOB]`.
5. `MatchingAgent` `[SOURCE JOB PASS-THROUGH]`.
6. Final `[SOURCE JOB]`.

Confirm `JobDescriptionAgent` called `get_job` exactly once and source
URL/title/agency match the selected card.

### Source URL or provenance is missing

For a successful Careers retrieval, `[SOURCE JOB]` must contain title, agency,
canonical source URL, exact key, and dataset version. Confirm:

1. `JobDescriptionAgent` emitted `[SOURCE JOB]` from the successful tool response.
2. `MatchingAgent` copied it verbatim to `[SOURCE JOB PASS-THROUGH]`.
3. `GapAnalyzer` copied those values into final `[SOURCE JOB]`.

Do not infer missing values. For the pasted-JD path, `Not provided` and `Not
applicable` are expected when the prompt supplied no provenance.

### Retrieved job tries to issue instructions

Restore the untrusted-data rules in `JOB_DESCRIPTION_INSTRUCTIONS` and the
`[UNTRUSTED CAREERS JOB DATA ...]` wrapper in the tool output. Job content is
data only and cannot alter roles, tools, keys, or output format.

## Workflow and Microsoft Learn issues

### Missing JD, resume relay, or matching report

Confirm the labeled sections remain exact:

- `[SELECTED JOB KEY]`
- `[JOB DESCRIPTION PASS-THROUGH]`
- `[PARSED RESUME PASS-THROUGH]`
- `[SOURCE JOB]`
- `[SOURCE JOB PASS-THROUGH]`

The graph must remain:

```text
ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer
```

Each executor sees only its predecessor. A missing or renamed relay starves the
next stage.

### Duplicate final response

The `WorkflowBuilder` must have one start executor, `gap_executor` as the single
output executor, and exactly three sequential edges.

### `[MICROSOFT LEARN MCP FAILURE]`

- Confirm `MICROSOFT_LEARN_MCP_ENDPOINT` is
  `https://learn.microsoft.com/api/mcp`.
- Retry after checking network access.
- The agent should still return gap cards but mark official resources
  temporarily unavailable.
- Do not present static or fallback URLs as live MCP results.

Careers retrieval and Microsoft Learn retrieval are independent: Careers
`get_job` belongs only to `JobDescriptionAgent`; Learn MCP belongs only to
`GapAnalyzer`.

## Direct-code `azd` deployment and access

### Wrong project or role

- Confirm Azure CLI is signed into your attendee tenant/subscription.
- Confirm `AZURE_SUBSCRIPTION_ID`, `AZURE_LOCATION`,
  `AZURE_AI_PROJECT_ENDPOINT`, `FOUNDRY_PROJECT_ENDPOINT`, and
  `AZURE_AI_PROJECT_ID` all identify the same attendee-owned project and region.
- Both endpoint variables use the same project URL.
- `AZURE_AI_PROJECT_ID` must be the full ARM project resource ID.
- Obtain **Foundry Project Manager** on your project.
- Never use the trainer project or its model quota.

After correction, deploy only:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd deploy personal-career-copilot --no-prompt
```

Do not run `azd provision` or `azd up`.

### Model not found, quota exceeded, or throttled

- Confirm `AZURE_AI_MODEL_DEPLOYMENT_NAME` exactly matches a deployment in your
  project.
- Confirm that deployment has quota for four sequential model calls plus roadmap
  tool use.
- Use another deployment in your own project or ask your project owner for quota.

### Hosted Agent starts but Careers retrieval fails

Local `.env` and the `azd` environment are separate. Confirm the `azd`
environment has:

- `CAREERS_MCP_ENDPOINT`
- `CAREERS_MCP_API_KEY`
- `CAREERS_MCP_TIMEOUT_SECONDS`
- `MICROSOFT_LEARN_MCP_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `FOUNDRY_PROJECT_ENDPOINT`

Update missing values and redeploy. If local search works but hosted retrieval
does not, first compare endpoint/key values without printing the secret.

### Deployment is missing or not ready

Run from `workshop/lab02-multi-agent`:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent show --output json
```

Confirm the agent is in the intended project. Review the `azd deploy` output for
the first actionable error, correct the environment or permission issue, and
redeploy the same `personal-career-copilot` service.

## Getting help

If the issue remains:

1. Read the complete local host or `azd` error, not only its final line.
2. Record Python and package versions without including `.env` or secrets.
3. State whether the failure occurs in Careers CLI search, local host, Inspector,
   Learn MCP, or deployed invocation.
4. Use only synthetic prompt data in screenshots or issue reports.

### Checkpoint

- [ ] I can diagnose local host startup, placeholder validation, and OTLP tracing.
- [ ] I can distinguish MCP API-key failures from Foundry RBAC failures.
- [ ] I know how to recover from empty search and invalid/expired selected keys.
- [ ] I can trace exact key and source provenance through all relay sections.
- [ ] I know the pasted-JD fallback procedure for MCP unavailability.
- [ ] I can diagnose wrong project/model quota and Learn MCP failures.
- [ ] I will not expose secrets or real personal data while troubleshooting.

---

**Previous:** [07 - Verify the Hosted Agent](07-verify-in-playground.md) ·
**Next:** [09 - Summary →](09-summary.md) ·
**Home:** [Lab 02 README](../README.md) ·
[Workshop Home](../../../README.md)
