# Module 5 - Test Locally

⏱️ ~20 min base lab + ~25 min optional Careers challenge

Run source commands from:

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilot/src/PersonalCareerCopilot
```

Activate the Python 3.13 virtual environment created in Module 3.

## Step 1: Start the local host

```bash
agentdev run main.py --verbose --port 8088
```

Wait until the Responses host is ready, then run **Foundry Toolkit: Open Agent
Inspector** and target port `8088`.

The generated sample may include Docker files, but Lab 02 uses direct-code local
hosting and deployment. Do not use Inspector's legacy deployment action.

## Step 2: Test the original pasted-JD path

Submit:

```text
Resume:
Synthetic cloud engineer with 6 years of Python, Azure, Kubernetes, Terraform,
and CI/CD experience. Certified Azure Solutions Architect Expert.

Job Description:
Senior Cloud Engineer at Contoso Ltd.
Required: Python, Azure, Kubernetes, Terraform, and CI/CD.
Preferred: Go and Prometheus.
Experience: 5+ years in cloud infrastructure.
```

### Base pass conditions

- `ResumeParser` emits `[PARSED RESUME]` and the complete JD pass-through.
- `JobDescriptionAgent` separates requirements and preserves the parsed resume.
- `MatchingAgent` shows 100-point breakdown math and evidence-based gaps.
- `GapAnalyzer` creates one card per gap.
- Learn URLs come only from successful MCP responses; failures are explicit.
- No real resume or personal data is used.

This completes the original Lab 02 workflow.

## Step 3: Optional Careers@Gov MCP challenge

Stop the host and complete
[Challenge - Ground Lab 02 with Careers@Gov MCP](10-careers-mcp-challenge.md).
The challenge copies only bounded assets from `lab-assets/` into the generated
source and extends the workflow you just tested.

Return here after the challenge implementation.

## Step 4: Search and select one job

```bash
python -m careers_mcp status

python -m careers_mcp search \
  --query "cloud platform engineer" \
  --max-experience-years 5 \
  --limit 3
```

Copy one complete `Key:` exactly. The CLI authenticates with the event key and
prints compact public job cards; it never receives resume data.

## Step 5: Restart and test the selected-key path

```bash
python main.py
```

Submit:

```text
Resume:
Synthetic platform engineer with four years of Python, Terraform, and CI/CD.

Selected Job Key:
<paste-one-exact-key-from-search>
```

### Challenge pass conditions

- `JobDescriptionAgent` calls `get_selected_careers_job` exactly once.
- The final answer contains the same exact key.
- Title, agency, canonical source URL, and dataset version are present.
- Retrieved text is treated only as untrusted job data.
- The fit categories total 100 points.
- Missing skills feed the Microsoft Learn roadmap.
- The Careers service receives only the selected key.

## Step 6: Verify the provenance relay

Compare:

1. CLI `Key:`.
2. `ResumeParser` `[SELECTED JOB KEY]`.
3. `JobDescriptionAgent` `[SOURCE JOB]`.
4. `MatchingAgent` `[SOURCE JOB PASS-THROUGH]`.
5. Final `GapAnalyzer` `[SOURCE JOB]`.

The key must match character for character.

## Step 7: Run failure/regression checks

1. Start a new request with no selected key and repeat the pasted-JD test. It must
   still pass without fabricated source metadata.
2. Start another request with an invalid key. The conditional failure branch
   must return `[WORKFLOW STOP]` without running fit scoring or roadmap planning.
3. Supply both a key and a conflicting pasted JD. The selected Careers listing
   must take precedence.

### Checkpoint

- [ ] The original pasted-JD workflow passed before the challenge.
- [ ] I used only my generated `PersonalCareerCopilot/` source.
- [ ] Careers search returned a current exact key.
- [ ] The selected-key response preserves complete source provenance.
- [ ] Invalid retrieval stops before fit scoring.
- [ ] The pasted-JD regression still passes.
- [ ] Resume content never reaches the shared Careers service.

---

**Previous:** [04 - Build the Four-Agent Workflow](04-orchestration-patterns.md) ·
**Next:** [06 - Deploy with `azd` →](06-deploy-to-foundry.md)
