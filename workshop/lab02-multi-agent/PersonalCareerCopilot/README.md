# PersonalCareerCopilot

A four-agent Microsoft Agent Framework workflow:

`ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer`

Learners search the trainer-hosted Careers MCP service locally, select a stable
job key, and submit that key with a synthetic resume. Only
`JobDescriptionAgent` can retrieve the selected job. `GapAnalyzer` continues to
use the Microsoft Learn MCP service for roadmap resources.

## Set up

Python 3.10 or later is required.

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilot
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```

Set placeholder values in `.env`; never commit the file:

```env
FOUNDRY_PROJECT_ENDPOINT=https://<foundry-resource>.services.ai.azure.com/api/projects/<project-name>
AZURE_AI_MODEL_DEPLOYMENT_NAME=<model-deployment-name>
CAREERS_MCP_ENDPOINT=https://<careers-mcp-host>/mcp
CAREERS_MCP_API_KEY=<careers-workshop-api-key>
CAREERS_MCP_TIMEOUT_SECONDS=10
MICROSOFT_LEARN_MCP_ENDPOINT=https://learn.microsoft.com/api/mcp
```

## Local two-step flow

### 1. Search and choose a stable key

The CLI sends `x-careers-workshop-key` through the MCP Streamable HTTP client
and prints no more than five compact cards:

```bash
python -m careers_mcp search \
  --query "cloud platform engineer" \
  --max-experience-years 5
```

Choose one exact `Key:` value. The service is job-discovery only: do not send a
resume or other personal data to it.

### 2. Run the agent and submit the selection

```bash
python -m debugpy --listen 127.0.0.1:5679 main.py --port 8088
```

Open Agent Inspector and send synthetic data in this shape:

```text
Resume:
Jane Doe
Cloud engineer with 4 years of experience building Python services and
Terraform-based platforms. Certified AWS Solutions Architect Associate.

Selected Job Key:
<paste-one-exact-key-from-the-search-output>
```

The workflow emits source title, agency, URL, job key, and dataset version in
the final roadmap. A pasted `Job Description:` remains supported only when no
selected key is supplied. If neither is present, the workflow asks for a search
and selection. MCP retrieval failures are surfaced and never replaced with
fabricated or fallback job data.

## Files

- `careers_mcp.py` — validated, bounded MCP client and learner CLI.
- `main.py` — sequential workflow and the single Careers agent tool.
- `.env.example` — credential-free configuration template.
- `.agentignore` — exclusions for direct-code Hosted Agent deployment.
- `requirements.txt` — exact tested runtime dependency versions.
- `tests/` — MCP client and instruction-contract tests.

Infrastructure and `azure.yaml` are intentionally outside this task. The old
container manifest path was removed so this folder has one deployment approach.

## Test

```bash
pip install -r requirements-dev.txt
pytest --basetemp=.pytest-tmp
```

## Evaluation assets

Southeast Asia does not currently support server-side synthetic dataset
generation. This folder includes a manual core smoke suite in `eval.yaml`, a
negative-path suite in `eval.coverage.yaml`, and a separate extended dataset.
Trainers can run the deployed-agent smoke suite with:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent eval run --config eval.yaml --no-wait --no-prompt
```

Run prompt-injection, invalid-key, and missing-selection coverage separately:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd env set LAST_EVAL_ID "" >/dev/null
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent eval run --config eval.coverage.yaml --no-wait --no-prompt
```

Treat any errored case or failed required criterion as a failed coverage gate.

References: [Foundry hosted Agent Framework agents](https://learn.microsoft.com/azure/foundry/how-to/develop/framework-hosted-agents?pivots=programming-language-python)
and the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).
