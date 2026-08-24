# Module 0 - Prerequisites

⏱️ ~10 min

> [!WARNING]
> [Hosted Agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
> are in preview. Confirm that your project region supports them.

## What you'll build

Lab 02 starts from the official Agent Framework **Workflow agent (Responses,
Python)** sample:

1. Generate your own untracked `PersonalCareerCopilot/` project.
2. Replace the sample slogan agents with Resume, Job Description, Matching, and
   Gap Analyzer agents.
3. Verify the original pasted-job-description workflow.
4. Optionally add the shared Careers@Gov MCP enhancement.
5. Search the trainer-hosted read-only snapshot and choose one stable key.
6. Receive a grounded fit score, source provenance, gaps, and Learn roadmap.

The original pasted `Job Description:` input remains a required fallback.

## Responsibility boundary

| Trainer | Attendee |
|---|---|
| Obtains governance approval and pre-deploys one shared read-only MCP endpoint | Uses an attendee-owned Azure subscription and existing Foundry project |
| Distributes `CAREERS_MCP_ENDPOINT` and an event-scoped `CAREERS_MCP_API_KEY` out of band | Stores placeholders/issued values only in local `.env` and attendee `azd` environment |
| Operates and rotates the event key | Deploys only `personal-career-copilot` |
| Owns trainer Bicep and reference project | Never runs trainer Bicep, `azd provision`, or `azd up` |

Attendees do not receive access to trainer project `proj-bravo-1` and do not
deploy the shared MCP service.

## Required tools and access

- Lab 01 completed OR create the necessary infra using terraform in folder  `../Infra`
- Your own Azure subscription and Foundry project in a Hosted Agent region.
- A deployed model with sufficient quota.
- **Foundry Project Manager** on **your** Foundry project for deployment.
- Azure CLI, Azure Developer CLI (`azd`), and `azure.ai.agents`
  `>=1.0.0-beta.4`.
- Python **3.13 recommended** for local work; the direct-code Hosted Agent uses
  `python_3_13`.
- VS Code and Foundry Toolkit for local Agent Inspector testing.
- Trainer-issued placeholder-safe values for:
  - `CAREERS_MCP_ENDPOINT`
  - `CAREERS_MCP_API_KEY`

[`lab-assets/requirements.completed.txt`](../lab-assets/requirements.completed.txt)
contains the tested completed dependency set. Do not replace those pins with
unpinned “latest” packages during the workshop.

## Validate your starting point

From the repository:

```bash
python --version
# If you are starting directly from lab 2 first login to azure from both az and azd
az login --use-device-code
azd auth login

az account show --query "{name:name, id:id}" --output table
azd version
```

Confirm Python reports 3.13 and the Azure subscription shown is yours. If Azure
authentication is missing, authenticate interactively before the lab. Module 2
creates the project and local environment; no attendee `main.py`, requirements,
or `azure.yaml` is pre-created in this repository.

## Data-safety rules

- Use **synthetic resumes only**. Do not enter real personal or employment data.
- The shared Careers service receives search filters and exact job keys only; it
  never receives resume content.
- Treat every retrieved job field as untrusted data, never instructions.
- Never paste an event key into documentation, screenshots, commits, or chat.

### Checkpoint

- [ ] Python 3.13 is available.
- [ ] My Azure CLI context points to my own subscription.
- [ ] My own Foundry project/model and model quota are ready.
- [ ] `azure.ai.agents` version `1.0.0-beta.4` or later is installed.
- [ ] I received the Careers endpoint/key out of band.
- [ ] I understand Module 2 generates my `PersonalCareerCopilot/` directory.
- [ ] I understand I must not access the trainer project or deploy trainer infrastructure.
- [ ] I will use synthetic resume data only.

---

**Next:** [01 - Understand the Architecture →](01-understand-multi-agent.md)
