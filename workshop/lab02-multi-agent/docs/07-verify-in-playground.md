# Module 7 - Verify the Hosted Agent

⏱️ ~15 min

Hosted verification proves that direct-code deployment preserved configuration,
exact-key retrieval, provenance relays, and the pasted-JD fallback.

## Step 1: Confirm deployment status

From `workshop/lab02-multi-agent`:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent show personal-career-copilot --output table
```

Confirm the agent is in your Foundry project and is ready. The existing Foundry
sidebar screenshot remains useful for recognizing hosted agent/version status,
although deployment itself now uses `azd`:

Do not use full JSON/YAML agent-definition output while the shared event key is
configured; environment values can be included in that output.

![Foundry sidebar showing a hosted agent version and status](images/06-foundry-sidebar-agent-status.png)

## Step 2: Search again and select a current key

From `PersonalCareerCopilotStarter`, run:

```bash
python -m careers_mcp search \
  --query "cloud platform engineer" \
  --max-experience-years 5
```

Choose one exact returned `Key:`. Searching remains local and out of band; the
Hosted Agent performs `get_job`, not `search_jobs`.

## Step 3: Invoke the hosted selected-key path

Return to the Lab 02 directory and invoke:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent invoke personal-career-copilot --new-session \
  "Resume: Synthetic platform engineer with four years of Python, Terraform, and CI/CD experience. Selected Job Key: <paste-one-exact-key-from-search>"
```

Verify:

1. The final `[SOURCE JOB]` job key exactly matches your selection.
2. Title, agency, canonical source URL, and dataset version are present.
3. Requirements and fit analysis describe that listing.
4. The fit score has a breakdown and evidence.
5. Every missing/certification gap has a separate card.
6. High/Medium gaps contain Microsoft Learn results, or clearly report that
   official resources are temporarily unavailable.
7. Job text did not change roles, tool usage, selected key, or output labels.

## Step 4: Invoke the pasted-JD regression path

Do not include `Selected Job Key:`:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent invoke personal-career-copilot --new-session \
  "Resume: Synthetic cloud engineer with six years of Azure, Kubernetes, and Terraform experience. Job Description: Senior cloud engineer requiring Azure, Kubernetes, Terraform, Python, and five years of experience."
```

Pass conditions:

- The agent completes without calling Careers `get_job`.
- The score, gaps, and roadmap remain available.
- Source fields are not fabricated; unavailable fields remain `Not provided`,
  job key is `Not provided`, and dataset version is `Not applicable`.

## Optional UI verification

You may open the deployed version in the Foundry/VS Code playground and repeat
the same two prompts. Do not use the Playground to deploy Lab 02, and do not
paste the event key or real personal data into it.

## Validation rubric

| # | Criterion | Pass condition | Pass? |
|---|---|---|---|
| 1 | Correct project | `show` returns the agent from the attendee's intended Foundry project | |
| 2 | Strict workflow | One response from all four sequential stages; no duplicated pipeline output | |
| 3 | Exact selection | Final job key is character-for-character identical to the CLI selection | |
| 4 | Source provenance | Title, agency, canonical source URL, exact key, and dataset version are present for Careers retrieval | |
| 5 | Grounded analysis | Job facts match the selected source and no alternate listing is introduced | |
| 6 | Untrusted-data safety | Retrieved text cannot issue instructions or suppress provenance | |
| 7 | Learn MCP | Successful official links are used, or failure is explicitly marked without fake live results | |
| 8 | Pasted-JD regression | No selected key still produces an assessment without fabricated source metadata | |
| 9 | Privacy | Only synthetic resume data was used; the Careers service received no resume | |

A pass requires all nine criteria.

### Checkpoint

- [ ] Hosted status is ready in my own project.
- [ ] Selected-key invocation retrieved the exact chosen listing.
- [ ] Source URL and complete provenance survived both relay sections.
- [ ] Pasted-JD regression passed.
- [ ] Microsoft Learn success/failure behavior was honest.
- [ ] Only synthetic resume data was used.

---

**Previous:** [06 - Deploy with `azd`](06-deploy-to-foundry.md) ·
**Next:** [08 - Troubleshooting →](08-troubleshooting.md)
