# Module 5 - Search & Test Locally

⏱️ ~20 min

Run every command in this module from
`workshop/lab02-multi-agent/PersonalCareerCopilot` with the Python 3.13 virtual
environment active and `.env` configured.

## Step 1: Search the shared Careers snapshot

```bash
python -m careers_mcp search \
  --query "cloud platform engineer" \
  --max-experience-years 5
```

The CLI authenticates with the event key and prints at most five compact cards.
Each card includes a stable `Key:`, title, agency, experience, canonical URL,
and optional metadata.

If the result is empty, adjust the query or remove a filter; do not invent a job
key. If the call fails, use [Module 8](08-troubleshooting.md).

## Step 2: Explicitly select one exact key

Copy one returned `Key:` value exactly. Do not edit its case, punctuation, or
three-part `platform:jobId:postingNo` structure.

The CLI performs discovery only. The agent must not select a job on your behalf.

## Step 3: Start the local agent

```bash
python -m debugpy --listen 127.0.0.1:5679 main.py --port 8088
```

Open Agent Inspector from the VS Code Command Palette and connect to
`http://localhost:8088`. Agent Inspector remains the supported local test
surface; its older **Deploy** action is not the Lab 02 deployment path.

The existing Inspector screenshots remain useful for recognizing the chat and
response panels, although pre-enhancement screenshots show the pasted-JD flow:

![Agent Inspector open and ready](images/04-debug-console-matching-input.png)

## Step 4: Test the selected-key path

Submit this shape in Agent Inspector, replacing only the key with the exact
value selected in Step 2:

```text
Resume:
Jane Doe
Cloud engineer with 4 years of experience building Python services and
Terraform-based platforms. Certified AWS Solutions Architect Associate.

Selected Job Key:
<paste-one-exact-key-from-the-search-output>
```

This is synthetic workshop data. Do not paste a real resume, contact details, or
employment history.

### Pass conditions

- The final answer has a fit score, gap cards, and roadmap.
- `[SOURCE JOB]` contains the exact selected key.
- Source title, agency, canonical URL, and dataset version are present.
- The facts correspond to that selected listing, not another search result.
- High/Medium gaps contain successful Microsoft Learn URLs, or are clearly
  marked temporarily unavailable if Learn MCP failed.
- No retrieved job text is followed as an instruction.

The Careers MCP receives only the selected key during this test. It never
receives the resume.

## Step 5: Test the pasted-JD regression path

Submit a new synthetic prompt with **no** `Selected Job Key:`:

```text
Resume:
Alex Chen
Cloud engineer with 6 years of experience in Python, Azure, Kubernetes,
Terraform, and CI/CD. Certified Azure Solutions Architect Expert.

Job Description:
Senior Cloud Engineer at Contoso Ltd.
Required: Python, Azure, Kubernetes, Terraform, and CI/CD.
Preferred: Go and Prometheus.
Experience: 5+ years in cloud infrastructure.
```

### Pass conditions

- The workflow uses the pasted JD and does not call Careers `get_job`.
- It still returns score, gaps, and roadmap.
- `[SOURCE JOB]` does not fabricate provenance: unspecified values are
  `Not provided`, job key is `Not provided`, and dataset version is
  `Not applicable`.

The older full-response screenshot is a useful visual reference for this
fallback path; wording may differ:

![Agent Inspector response with fit score and roadmap](images/05-inspector-test1-complete-response.png)

## Step 6: Negative selected-key check

Submit a syntactically invalid selected key with a synthetic resume. The agent
must report that retrieval failed or ask for a valid selection. It must not
fabricate a listing and must not silently use a pasted JD.

### Checkpoint

- [ ] Search returned job cards and I chose one exact stable key.
- [ ] I used only a synthetic resume.
- [ ] The selected-key result contains the exact key and complete provenance.
- [ ] Retrieved job content did not alter instructions or routing.
- [ ] The pasted-JD regression test passed without fabricated source metadata.
- [ ] Invalid key handling did not fabricate or silently switch jobs.
- [ ] The shared Careers service never received resume data.

---

**Previous:** [04 - Orchestration & Relays](04-orchestration-patterns.md) ·
**Next:** [06 - Deploy with `azd` →](06-deploy-to-foundry.md)
