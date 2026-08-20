# Trainer deployment

The repository-root `azure.yaml` is the trainer-only `azd` project. It deploys
one shared Careers job MCP Container App and one reference Hosted Agent.
Attendees use the agent-only `workshop/lab02-multi-agent/azure.yaml` project
instead.

## Existing resources

The Bicep template references, but does not create:

- Resource group: `rg-oceans-mcp-demo`
- Container Apps environment: `cae-oceans-mcp-demo-clckvj`
- ACR: `acrmcpodjhd42rocw6g`
- Foundry project:
  `https://foundry-bravo-1.services.ai.azure.com/api/projects/proj-bravo-1`
- Model deployment: `gpt-5.4-1`

It creates exactly one Container App and one AcrPull role assignment. Obtain the
tenant policy exemption for those resource IDs before provisioning.

## Prerequisites

- Contributor or equivalent rights on `rg-oceans-mcp-demo`
- `AcrPush` on `acrmcpodjhd42rocw6g`
- Role Based Access Control Administrator, User Access Administrator, or Owner
  at the ACR scope to create the AcrPull role assignment
- Foundry Project Manager on `proj-bravo-1`
- The Container Apps environment usage check from the approved deployment plan
- A 32-character or longer event key held outside source control
- `AZURE_DEV_USER_AGENT=microsoft_foundry_skill` set inline on every `azd`
  command

## Configure

Run from the repository root. Authenticate manually before continuing;
automation must not run `az login` or `azd auth login` for you.

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd env new careers-workshop --no-prompt
AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd env set \
  AZURE_SUBSCRIPTION_ID=e49ea726-8fd5-4a46-b267-db602e7b8ef1 \
  AZURE_TENANT_ID=323626f5-1bfe-48cd-8902-ddfdfd44e1ce \
  AZURE_LOCATION=southeastasia \
  AZURE_RESOURCE_GROUP=rg-oceans-mcp-demo \
  AZURE_AI_PROJECT_ENDPOINT=https://foundry-bravo-1.services.ai.azure.com/api/projects/proj-bravo-1 \
  FOUNDRY_PROJECT_ENDPOINT=https://foundry-bravo-1.services.ai.azure.com/api/projects/proj-bravo-1 \
  AZURE_AI_PROJECT_ID='/subscriptions/e49ea726-8fd5-4a46-b267-db602e7b8ef1/resourceGroups/bravo-ai-rg/providers/Microsoft.CognitiveServices/accounts/foundry-bravo-1/projects/proj-bravo-1' \
  AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5.4-1 \
  AZURE_CONTAINER_ENVIRONMENT_NAME=cae-oceans-mcp-demo-clckvj \
  AZURE_CONTAINER_REGISTRY_NAME=acrmcpodjhd42rocw6g \
  CAREERS_MCP_CONTAINER_APP_NAME=ca-careers-job-mcp-workshop \
  CAREERS_MCP_TIMEOUT_SECONDS=10 \
  MICROSOFT_LEARN_MCP_ENDPOINT=https://learn.microsoft.com/api/mcp
```

Set the real key separately so it is not copied into scripts or shell history:

```bash
read -rsp "Workshop API key: " CAREERS_KEY && echo
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd env set CAREERS_MCP_API_KEY "$CAREERS_KEY"
unset CAREERS_KEY
```

## Build the frozen index

Use the approved upstream commit and generated timestamp before building the
container:

```bash
cd workshop/lab02-multi-agent/careers-job-mcp
PYTHONPATH=src .venv/bin/python -m careers_job_mcp.build_index \
  --source-commit 84de3599f6927aa48be6f03c4bbb3c58d3965ba5 \
  --generated-at 2026-08-26T00:00:00Z \
  --output data/careers-jobs.sqlite3
cd ../../..
```

Replace the development commit with the final approved event snapshot.

## Provision and deploy

1. Preview Bicep and confirm it contains only the new Container App and AcrPull
   assignment:

   ```bash
   AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd provision --preview --no-prompt
   ```

2. Provision the public placeholder revision and system identity:

   ```bash
   AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd provision --no-prompt
   ```

3. Wait for the AcrPull role assignment to propagate and confirm the new app
   identity can pull from ACR.
4. Attach the existing registry to the Container App using its system identity:

   ```bash
   az containerapp registry set \
     --subscription e49ea726-8fd5-4a46-b267-db602e7b8ef1 \
     --resource-group rg-oceans-mcp-demo \
     --name ca-careers-job-mcp-workshop \
     --server acrmcpodjhd42rocw6g.azurecr.io \
     --identity system
   ```

5. Build, push, and activate the private MCP image:

   ```bash
   AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd deploy careers-job-mcp --no-prompt
   ```

6. Verify `/healthz`, authenticated `/readyz`, MCP `tools/list`, and all three
   tools before deploying the reference agent.
7. Deploy and invoke the reference agent:

   ```bash
   AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd deploy personal-career-copilot-reference --no-prompt
   AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd ai agent invoke \
     personal-career-copilot-reference \
     "Use a synthetic resume and an explicitly selected job key."
   ```

## Evaluation

Server-side synthetic dataset generation is unavailable in Southeast Asia. The
reference agent therefore includes a manual fallback:

- `PersonalCareerCopilot/eval.yaml`
- `PersonalCareerCopilot/eval.coverage.yaml`
- `.foundry/datasets/careers-job-fit-smoke.jsonl`
- `.foundry/datasets/careers-job-fit-coverage.jsonl`

Run the core smoke suite from the repository root:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
  azd ai agent eval run \
  --config eval.yaml \
  --name careers-job-fit-core-smoke \
  --no-wait \
  --no-prompt
```

The CLI resolves `eval.yaml` relative to the selected agent source folder. Use
`azd ai agent eval list` and `azd ai agent eval show` to monitor the run.
Clear `LAST_EVAL_ID` before switching to `eval.coverage.yaml`, otherwise the
CLI reuses the prior evaluator definition.

Container App revisions and immutable image tags provide rollback. Cleanup is
destructive and is intentionally not included here.
