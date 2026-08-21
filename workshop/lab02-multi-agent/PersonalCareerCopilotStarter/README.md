# PersonalCareerCopilotStarter

This is the attendee working directory for Lab 02.

It begins as the runnable **original** Resume → Job Fit Evaluator:

`ResumeParser → JobDescriptionAgent → MatchingAgent → GapAnalyzer`

The baseline accepts a synthetic resume plus a pasted job description. Attendees
then complete the optional Careers@Gov MCP challenge in this folder. The finished
reference remains in [`../PersonalCareerCopilot`](../PersonalCareerCopilot).

## Set up

```bash
cd workshop/lab02-multi-agent/PersonalCareerCopilotStarter
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Replace the project/model placeholders in `.env`. Keep the trainer-issued
Careers endpoint and key there for the challenge; never commit `.env`.

## Prove the original Lab 02 path

Start the host:

```bash
python main.py
```

Submit a synthetic resume and pasted `Job Description:` in Agent Inspector.
Confirm the original fit score, gaps, and Microsoft Learn roadmap work before
adding Careers data.

## Start the Careers MCP challenge

Copy the provided bounded client into your working directory:

```bash
cp ../PersonalCareerCopilot/careers_mcp.py .
```

Then complete the numbered TODOs in `main.py` using the
[Careers@Gov MCP challenge](../docs/10-careers-mcp-challenge.md).

Do not edit the solution directory during the lab. Use it only after attempting
each task or during the trainer debrief.

## Deploy

The attendee [`../azure.yaml`](../azure.yaml) points to this starter directory.
After the challenge works locally, run deployment commands from the Lab 02 root.
