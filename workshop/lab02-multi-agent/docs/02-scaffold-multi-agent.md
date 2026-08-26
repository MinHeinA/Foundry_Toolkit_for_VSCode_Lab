# Module 2 - Scaffold the Attendee Workflow Project

⏱️ ~15 min

Create your own Lab 02 project from the official Microsoft Foundry sample. The
repository intentionally does not contain an attendee `PersonalCareerCopilot/`
directory.

## Step 1: Confirm the workflow sample

From `workshop/lab02-multi-agent`:

```bash
# From base directory cd to workshop/lab02-multi-agent
cd workshop/lab02-multi-agent
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent sample list --language python --output text
```

PowerShell:

```powershell
$env:AZURE_DEV_USER_AGENT = "microsoft_foundry_skill"
azd ai agent sample list --language python --output text
Remove-Item Env:AZURE_DEV_USER_AGENT
```

Select **Workflow agent (Responses, Agent Framework, Python)**. This lab pins
its current manifest:

```text
https://github.com/microsoft-foundry/foundry-samples/blob/main/samples/python/hosted-agents/agent-framework/responses/05-workflows/azure.yaml
```

## Step 2: Generate the project

Confirm neither `agent-framework-workflows-responses/` nor
`PersonalCareerCopilot/` already exists. Do not rerun initialization over an
existing project; the extension can create duplicate services.

```bash
test ! -e agent-framework-workflows-responses
test ! -e PersonalCareerCopilot
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent init --no-prompt \
  -m "https://github.com/microsoft-foundry/foundry-samples/blob/main/samples/python/hosted-agents/agent-framework/responses/05-workflows/azure.yaml" \
  --deploy-mode code \
  --runtime python_3_13 \
  --entry-point main.py
```

PowerShell:

```powershell
if (Test-Path agent-framework-workflows-responses) { throw "Generated folder already exists." }
if (Test-Path PersonalCareerCopilot) { throw "Lab 02 project already exists." }
$env:AZURE_DEV_USER_AGENT = "microsoft_foundry_skill"
azd ai agent init --no-prompt `
  -m "https://github.com/microsoft-foundry/foundry-samples/blob/main/samples/python/hosted-agents/agent-framework/responses/05-workflows/azure.yaml" `
  --deploy-mode code `
  --runtime python_3_13 `
  --entry-point main.py
Remove-Item Env:AZURE_DEV_USER_AGENT
```

The current scaffold creates `agent-framework-workflows-responses/`, including
its own `azure.yaml`, local azd environment, source tree, `main.py`, requirements,
and deployment metadata.

If the command reports missing subscription/location values, continue. Module 6
binds the generated project to the existing Lab 01 Foundry project before
deployment.

## Step 3: Normalize the workshop names

macOS/Linux:

```bash
mv agent-framework-workflows-responses PersonalCareerCopilot
cd PersonalCareerCopilot
mv src/agent-framework-workflows-responses src/PersonalCareerCopilot
```

Windows PowerShell:

```powershell
Rename-Item agent-framework-workflows-responses PersonalCareerCopilot
Set-Location PersonalCareerCopilot
Rename-Item src/agent-framework-workflows-responses PersonalCareerCopilot
```

The expected structure is:

```text
PersonalCareerCopilot/
├── azure.yaml
├── .azure/
└── src/
    └── PersonalCareerCopilot/
        ├── main.py
        ├── requirements.txt
        └── .env.example
```

## Step 4: Apply attendee-only assets

The generated sample can provision its own AI project. Lab 02 instead reuses the
attendee's existing Lab 01 project, so replace the generated manifest with the
attendee-only reference:

macOS/Linux:

```bash
cp ../lab-assets/azure.attendee.yaml azure.yaml
cp ../lab-assets/requirements.completed.txt \
  src/PersonalCareerCopilot/requirements.txt
cp ../lab-assets/.env.example src/PersonalCareerCopilot/.env
cp ../lab-assets/.agentignore src/PersonalCareerCopilot/.agentignore
```

Windows PowerShell:

```powershell
Copy-Item ../lab-assets/azure.attendee.yaml azure.yaml -Force
Copy-Item ../lab-assets/requirements.completed.txt `
  src/PersonalCareerCopilot/requirements.txt -Force
Copy-Item ../lab-assets/.env.example `
  src/PersonalCareerCopilot/.env -Force
Copy-Item ../lab-assets/.agentignore `
  src/PersonalCareerCopilot/.agentignore -Force
```

The attendee manifest:

- contains only `personal-career-copilot`;
- uses direct-code runtime `python_3_13`;
- points to `src/PersonalCareerCopilot/main.py`;
- contains no `infra` or `ai-project` service;
- receives model and MCP values from the attendee azd environment.

## Step 5: Preserve the generated starting point

Open `src/PersonalCareerCopilot/main.py`. It is the generated slogan workflow,
not the Resume → Job Fit Evaluator. Module 3 replaces its three sample agents
with the four Lab 02 agents.

Do not copy the completed `main.py`. Use
[`PersonalCareerCopilotCompleted`](../PersonalCareerCopilotCompleted) only after
attempting each module or during the trainer debrief.

The generated `PersonalCareerCopilot/` directory is ignored by the parent
workshop repository, but it remains its own local azd/git project.

### Checkpoint

- [ ] The official workflow sample generated my own project.
- [ ] The outer directory is `PersonalCareerCopilot/`.
- [ ] Source is under `src/PersonalCareerCopilot/`.
- [ ] `azure.yaml` came from `lab-assets/azure.attendee.yaml`.
- [ ] `.agentignore` excludes `.env`, virtual environments, tests, and `.vscode`.
- [ ] The manifest has no infrastructure section.
- [ ] `main.py` still contains the generated slogan workflow.
- [ ] I have not copied code from `PersonalCareerCopilotCompleted/`.

---

**Previous:** [01 - Understand the Architecture](01-understand-multi-agent.md) ·
**Next:** [03 - Configure Agents & Environment →](03-configure-agents.md)
