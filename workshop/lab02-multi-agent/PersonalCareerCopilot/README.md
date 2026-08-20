# PersonalCareerCopilot

A four-agent Microsoft Agent Framework workflow:

`ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer`

Learners search the trainer-hosted Careers MCP service out of band, select one
stable job key, and submit that exact key with a synthetic resume. Only
`JobDescriptionAgent` can retrieve the selected listing. `GapAnalyzer` uses the
Microsoft Learn MCP service for official roadmap resources.

## Set up

Use Python 3.13, which matches the direct-code Hosted Agent runtime:

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilot
python3.13 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```

Replace every placeholder copied from [`.env.example`](.env.example):

```env
FOUNDRY_PROJECT_ENDPOINT=https://<foundry-resource>.services.ai.azure.com/api/projects/<project-name>
AZURE_AI_MODEL_DEPLOYMENT_NAME=<model-deployment-name>
CAREERS_MCP_ENDPOINT=https://<careers-mcp-host>/mcp
CAREERS_MCP_API_KEY=<careers-workshop-api-key>
CAREERS_MCP_TIMEOUT_SECONDS=10
MICROSOFT_LEARN_MCP_ENDPOINT=https://learn.microsoft.com/api/mcp
```

Use your own attendee Foundry project/model and the trainer-provided Careers
endpoint/key. Never commit `.env` or use real resume data.

## Search, host, and test locally

### 1. Search and select one exact key

```bash
python -m careers_mcp search \
  --query "cloud platform engineer" \
  --max-experience-years 5
```

Copy one complete `Key:` value without changing its case or punctuation. The
Careers service receives search filters or that key only, never the resume.

### 2. Start the local agent host

```bash
python main.py
```

For breakpoint attach from the command line, start the direct debug server:

```bash
python -m debugpy --listen 127.0.0.1:5679 main.py --port 8088
```

Alternatively, run the VS Code task **Run Agent HTTP Server**. For full F5
debugging, select **Debug Local Agent HTTP Server**; it starts the direct local
host under `debugpy`, opens Agent Inspector, and attaches the debugger.

### 3. Exercise both input paths

For the selected-key path, send synthetic data in Agent Inspector:

```text
Resume:
Jane Doe
Cloud engineer with 4 years of Python, Terraform, and platform experience.

Selected Job Key:
<paste-one-exact-key-from-the-search-output>
```

The final `[SOURCE JOB]` must preserve the title, agency, canonical URL, exact
job key, and dataset version. A pasted `Job Description:` remains supported only
when no selected key is supplied. If selected-key retrieval fails, the workflow
reports the failure and does not silently switch to pasted content.

## Files

- `main.py` — strict four-agent workflow, Careers retrieval tool, and Learn tool.
- `careers_mcp.py` — validated Careers MCP client and learner search CLI.
- `.env.example` — credential-free local/runtime configuration template.
- `.vscode/` — local host task, Inspector launch, and interpreter settings.
- `.agentignore` — direct-code upload exclusions.
- `requirements.txt` / `requirements-dev.txt` — pinned runtime and test dependencies.
- `tests/` — MCP client and instruction-contract tests.
- `eval.yaml` / `eval.coverage.yaml` — core and negative-path evaluation configs.
- `.foundry/datasets/careers-job-fit-smoke.jsonl` — core smoke dataset.
- `.foundry/datasets/careers-job-fit-coverage.jsonl` — negative coverage dataset.
- `.foundry/datasets/careers-job-fit-extended.jsonl` — optional extended cases.

The direct-code deployment manifest is the parent [`../azure.yaml`](../azure.yaml).
This project intentionally has no `agent.yaml` or Dockerfile.

## Run tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest --basetemp=.pytest-tmp
```

## Deploy and evaluate

Deploy only the direct-code agent from the parent directory:

```bash
cd ..
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd deploy personal-career-copilot --no-prompt
```

After configuring the deployed-agent metadata in the evaluation files, run the
core suite:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent eval run --config eval.yaml --no-wait --no-prompt
```

Clear `LAST_EVAL_ID` before running the independent coverage suite:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd env set LAST_EVAL_ID ""
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent eval run --config eval.coverage.yaml --no-wait --no-prompt
```

## References

- [Develop Agent Framework hosted agents in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/how-to/develop/framework-hosted-agents?pivots=programming-language-python)
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Lab 02 walkthrough](../docs/README.md)
