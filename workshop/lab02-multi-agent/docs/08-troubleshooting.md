# Module 8 - Troubleshooting

Use this guide for the implemented Careers MCP and direct-code Hosted Agent
path. Never post the event key, `.env`, tokens, or real resume data in an issue.

## Careers MCP configuration and authentication

### `CAREERS_MCP_ENDPOINT is required` or `CAREERS_MCP_API_KEY is required`

- Confirm `.env` is in `PersonalCareerCopilot/`, beside `main.py`.
- Copy from `.env.example` and replace every placeholder.
- Confirm the key has no surrounding whitespace.
- Restart the CLI/server after changing `.env`.

### `CAREERS_MCP_API_KEY is invalid`

The local client rejects empty, placeholder-like, oversized, or unsafe values.
Copy the event key again from the trainer's out-of-band channel. Do not add
quotes to the value inside `.env` unless your environment parser requires them.

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
- Use the pasted `Job Description:` fallback until the trainer restores service.

When a selected key is present and retrieval fails, the agent intentionally does
not silently switch to pasted JD content. Start a new fallback request without a
selected key.

## Search and selected-key issues

### `No matching jobs found`

An empty search is valid. Broaden `--query`, remove optional filters, or increase
`--max-experience-years` if appropriate. Never invent a key. The service returns
at most five cards.

### `job_key has an invalid format`

Copy the complete `Key:` from CLI output. A stable key has exactly three
colon-separated components. Do not change case, punctuation, or whitespace.

### Selected key is no longer found

The key may not exist in the trainer's frozen event snapshot, may be truncated,
or may come from an older snapshot. Run the CLI against the current endpoint,
select a returned key, and resubmit. Do not substitute a similar listing.

### Agent retrieves the wrong listing

- Compare Agent Inspector input, `[SELECTED JOB KEY]`, `[SOURCE JOB]`, and final
  `[SOURCE JOB]` character for character.
- Confirm `ResumeParser` did not alter the key.
- Confirm `JobDescriptionAgent` called `get_job` exactly once.
- Confirm source URL/title/agency match the selected CLI card.

If any key changes between relays, restore the instruction blocks from
[`PersonalCareerCopilot/main.py`](../PersonalCareerCopilot/main.py).

### Source URL or provenance is missing

For a successful Careers retrieval, `[SOURCE JOB]` must contain title, agency,
canonical source URL, exact key, and dataset version. Check:

1. `JobDescriptionAgent` emitted `[SOURCE JOB]` from the tool response.
2. `MatchingAgent` copied it verbatim to `[SOURCE JOB PASS-THROUGH]`.
3. `GapAnalyzer` copied those values into final `[SOURCE JOB]`.

Do not infer missing values. For the pasted-JD path, `Not provided` and
`Not applicable` are expected when the prompt supplied no provenance.

## Workflow and output issues

### Missing JD or matching report

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

Compare the `WorkflowBuilder` block with the reference `main.py`. It must have
one start executor, `gap_executor` as the single output executor, and exactly the
three sequential edges shown above.

### Retrieved job tries to issue instructions

Restore the untrusted-data rules in `JOB_DESCRIPTION_INSTRUCTIONS` and the
`[UNTRUSTED CAREERS JOB DATA ...]` wrapper in the tool output. Job content is
data only and cannot alter roles, tools, keys, or output format.

## Microsoft Learn MCP

### `[MICROSOFT LEARN MCP FAILURE]`

- Confirm `MICROSOFT_LEARN_MCP_ENDPOINT` is
  `https://learn.microsoft.com/api/mcp`.
- Retry after checking network access.
- The agent should still return gap cards but mark official resources
  temporarily unavailable.
- Do not present static/fallback URLs as if they were live MCP results.

Careers retrieval and Microsoft Learn retrieval are independent: Careers
`get_job` belongs only to `JobDescriptionAgent`; Learn MCP belongs only to
`GapAnalyzer`.

## Foundry deployment and access

### Wrong project or role

- Confirm Azure CLI is signed into your attendee tenant/subscription.
- Confirm `AZURE_SUBSCRIPTION_ID`, `AZURE_AI_PROJECT_ENDPOINT`,
  `FOUNDRY_PROJECT_ENDPOINT`, and `AZURE_AI_PROJECT_ID` identify the same
  attendee-owned Foundry project and region.
- Confirm the ID is the full ARM project resource ID, not a display name.
- Obtain **Foundry Project Manager** on that project for deployment.
- Never use trainer project `proj-bravo-1`.

After correction, deploy again with only:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd deploy personal-career-copilot --no-prompt
```

### Model not found, quota exceeded, or throttled

- Confirm `AZURE_AI_MODEL_DEPLOYMENT_NAME` exactly matches a deployment in your
  project.
- Confirm that deployment has available request/token quota for four sequential
  model calls plus roadmap tool use.
- Use another deployment in your own project or ask your subscription/project
  owner for quota. Trainer model quota is not shared with attendees.

### Hosted Agent starts but Careers retrieval fails

The local `.env` and `azd` environment are separate. Confirm the `azd`
environment contains:

- `CAREERS_MCP_ENDPOINT`
- `CAREERS_MCP_API_KEY`
- `CAREERS_MCP_TIMEOUT_SECONDS`
- `MICROSOFT_LEARN_MCP_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

Update missing values and redeploy. Do not run `azd provision` or `azd up`.

## Runtime and package issues

- Use Python 3.13 locally.
- Hosted direct code uses `python_3_13`.
- Install `requirements.txt` as-is; packages are pinned.
- If imports fail, recreate the virtual environment and reinstall the pinned
  requirements rather than upgrading individual packages.

### Checkpoint

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
