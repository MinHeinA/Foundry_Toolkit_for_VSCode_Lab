# Lab 02 - Multi-Agent Workflow: Resume → Job Fit Evaluator

## Full learning path

Build, test, and deploy one direct-code Hosted Agent with four agents in a strict
sequential workflow. Search the trainer-hosted Careers MCP out of band, select
one stable job key, and keep the pasted-job-description regression path.

> **Prerequisite:** Complete [Lab 01](../../lab01-single-agent/README.md). Lab 02
> attendees use their own subscription, Foundry project, and model.

| # | Module | What you'll do |
|---|---|---|
| 0 | [Prerequisites](00-prerequisites.md) | Verify Python 3.13, your project/model, trainer-issued Careers settings, and privacy rules |
| 1 | [Understand the Architecture](01-understand-multi-agent.md) | Trace CLI search, exact selection, four sequential agents, both MCP services, and provenance relays |
| 2 | [Scaffold the Attendee Project](02-scaffold-multi-agent.md) | Generate `PersonalCareerCopilot/` from the official workflow sample and apply attendee assets |
| 3 | [Configure Agents & Environment](03-configure-agents.md) | Replace the sample agents with the Resume/JD/Matching/Gap contracts and configure `.env` |
| 4 | [Orchestration & Relays](04-orchestration-patterns.md) | Build the strict four-agent chain and labeled relay sections |
| 5 | [Test Locally](05-test-locally.md) | Prove the original pasted-JD workflow, then optionally test Careers exact-key retrieval |
| 6 | [Deploy with `azd`](06-deploy-to-foundry.md) | Target your existing Foundry project and deploy only the direct-code Hosted Agent |
| 7 | [Verify the Hosted Agent](07-verify-in-playground.md) | Show status, invoke with the exact key, and validate provenance plus fallback |
| 8 | [Troubleshooting](08-troubleshooting.md) | Diagnose Careers auth/search/key errors, Foundry role/quota issues, relays, and Learn MCP |
| 9 | [Summary & Next Steps](09-summary.md) | Complete the security, provenance, exact-key, deployment, and regression checklists |
| 10 | [Careers@Gov MCP Challenge](10-careers-mcp-challenge.md) | Compare the original pasted-JD flow with exact-key retrieval, source provenance, and regression-safe fallback |

---

**Back to:** [Lab 02 README](../README.md) ·
[Workshop Home](../../../README.md)
