# Module 0 - Prerequisites

⏱️ ~10 min

> [!WARNING]
> [Hosted Agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
> are in preview. Confirm that your project region supports them.

## What you'll build

Lab 02 extends the sequential Resume → Job Fit Evaluator with an optional shared
Careers@Gov MCP enhancement:

1. Run the original pasted-job-description workflow from the attendee starter.
2. Complete the numbered Careers MCP TODOs without editing the solution.
3. Search the trainer-hosted read-only job snapshot from a local CLI.
4. Explicitly choose one returned stable job key.
5. Give Agent Inspector a synthetic resume and `Selected Job Key:`.
6. Let `JobDescriptionAgent` retrieve exactly that listing.
7. Receive a fit score, source provenance, gaps, and a Microsoft Learn roadmap.

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

- Lab 01 completed.
- Your own Azure subscription and Foundry project in a Hosted Agent region.
- A deployed model with sufficient quota.
- **Foundry Project Manager** on **your** Foundry project for deployment.
- Azure CLI, Azure Developer CLI (`azd`), and the current Foundry `azd`
  extension declared by [`../azure.yaml`](../azure.yaml).
- Python **3.13 recommended** for local work; the direct-code Hosted Agent uses
  `python_3_13`.
- VS Code and Foundry Toolkit for local Agent Inspector testing.
- Trainer-issued placeholder-safe values for:
  - `CAREERS_MCP_ENDPOINT`
  - `CAREERS_MCP_API_KEY`

The packages in
[`PersonalCareerCopilotStarter/requirements.txt`](../PersonalCareerCopilotStarter/requirements.txt)
are pinned to tested versions. Do not replace them with unpinned “latest”
packages during the workshop.

## Validate your starting point

From the repository:

```bash
python --version
az account show --query "{name:name, id:id}" --output table
azd version
```

Confirm Python reports 3.13 and the Azure subscription shown is yours. If Azure
authentication is missing, authenticate interactively before the lab.

Copy the environment template, but do not commit `.env`:

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilotStarter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows users can activate with `.\.venv\Scripts\Activate.ps1` and copy with
`copy .env.example .env`.

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
- [ ] I received the Careers endpoint/key out of band.
- [ ] I understand I must not access the trainer project or deploy trainer infrastructure.
- [ ] I will use synthetic resume data only.

---

**Next:** [01 - Understand the Architecture →](01-understand-multi-agent.md)
