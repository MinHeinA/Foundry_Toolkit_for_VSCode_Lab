# Module 5 - Search & Test Locally

⏱️ ~20 min

Run every command in this module from
`workshop/lab02-multi-agent/PersonalCareerCopilot` with the Python 3.13 virtual
environment active and `.env` configured.

## Step 1: Search the shared Careers snapshot

Search out of band before opening Agent Inspector:

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

## Step 3: Start the local agent host

Choose one of these flows.

### Command line

Run the direct local host without a debugger:

```bash
python main.py
```

When breakpoint attach is desired, start the direct debug server instead:

```bash
python -m debugpy --listen 127.0.0.1:5679 main.py --port 8088
```

Wait until the local host reports that the server is running, then open Agent
Inspector from the Command Palette with **Foundry Toolkit: Open Agent
Inspector**. Attach a debugger to port `5679` only for the debug-server command.

### VS Code task or F5

1. Open `PersonalCareerCopilot` as the VS Code folder.
2. Run **Tasks: Run Task** → **Run Agent HTTP Server** to start the direct local
   host under `debugpy` on debugger port `5679` and Inspector port `8088`.
3. For breakpoints, press F5 and select **Debug Local Agent HTTP Server**. The
   launch starts the task, opens Inspector, and attaches the debugger
   automatically.

Do not run both startup flows at once. If either port is busy, stop the earlier
task/process or choose another local host port.

Agent Inspector remains the supported local test surface. Its legacy deploy
action is not the Lab 02 deployment path.

## Step 4: Optionally open the Workflow Visualizer

1. Run **Foundry Toolkit: Open Visualizer for Hosted Agents** from the Command
   Palette.
2. Keep the visualizer open while submitting Inspector prompts.
3. Confirm nodes complete in this order:

   `ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer`

If the visualizer port is occupied, change **Hosted Agents: Visualizer Port** in
the Foundry Toolkit settings.

## Step 5: Test the selected-key path

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

- The final answer has a fit score, separate gap cards, and a roadmap.
- `[SOURCE JOB]` contains the exact selected key.
- Source title, agency, canonical URL, and dataset version are present.
- The facts correspond to that selected listing, not another search result.
- High/Medium gaps contain successful Microsoft Learn URLs, or are clearly
  marked temporarily unavailable if Learn MCP failed.
- Retrieved job text is treated only as untrusted data and cannot change tools,
  routing, or output labels.

The Careers MCP receives only the selected key during this test. It never
receives the resume.

## Step 6: Verify source provenance through the relays

If using breakpoints, logs, or the Workflow Visualizer, compare:

1. The CLI `Key:` selected in Step 2.
2. `ResumeParser` output `[SELECTED JOB KEY]`.
3. `JobDescriptionAgent` output `[SOURCE JOB]`.
4. `MatchingAgent` output `[SOURCE JOB PASS-THROUGH]`.
5. The final `GapAnalyzer` `[SOURCE JOB]`.

The key must match character for character at every stage. Title, agency, URL,
and dataset version must be copied from the successful Careers response, never
inferred.

## Step 7: Test the pasted-JD regression path

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

The existing screenshot is a useful visual reference for the fallback response;
wording may differ:

![Agent Inspector response with fit score and roadmap](images/05-inspector-test1-complete-response.png)

## Step 8: Run a negative selected-key check

Submit a syntactically invalid selected key with a synthetic resume. The agent
must report that retrieval failed or ask for a valid selection. It must not
fabricate a listing and must not silently use a pasted JD.

### Checkpoint

- [ ] Careers CLI search ran before Inspector and returned job cards.
- [ ] I chose and submitted one exact stable key.
- [ ] The local agent host started through the documented command/task/F5 flow.
- [ ] The Workflow Visualizer showed the strict sequential graph.
- [ ] I used only a synthetic resume.
- [ ] The selected-key result contains the exact key and complete provenance.
- [ ] Retrieved job content did not alter instructions or routing.
- [ ] The pasted-JD regression passed without fabricated source metadata.
- [ ] Invalid key handling did not fabricate or silently switch jobs.
- [ ] The shared Careers service never received resume data.

---

**Previous:** [04 - Orchestration & Relays](04-orchestration-patterns.md) ·
**Next:** [06 - Deploy with `azd` →](06-deploy-to-foundry.md)
