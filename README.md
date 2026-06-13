# CAS Reference Product

Public v0.1 reference application for the Coding Autopilot System and Microsoft Foundry Next Gen Agents.

It runs a useful deterministic workflow locally, emits canonical [`cas-contracts`](https://github.com/Coding-Autopilot-System/cas-contracts) v0.1 lifecycle events, and includes a Foundry adapter that invokes a Next Gen agent reference through the project Responses client. It is designed for the Container Apps and managed identity boundary supplied by [`cas-platform`](https://github.com/Coding-Autopilot-System/cas-platform).

## What It Demonstrates

- `WorkflowAgentService` application boundary with local and Foundry Next Gen adapters.
- System-assigned managed identity in Azure; no embedded secrets, keys, or tokens.
- Canonical `PromptEnvelope` input and `RunEvent` lifecycle output.
- OpenTelemetry spans and optional Application Insights export.
- Liveness, readiness, tests, Dockerfile, CI, architecture, threat model, and operations.
- Explicit non-deploying interface for `cas-platform`.

This project does not use Classic Assistants APIs and does not deploy Azure resources.

## Run Locally

Prerequisites: Python 3.12 and PowerShell.

```powershell
./scripts/validate.ps1
./scripts/run-local.ps1
```

In another terminal:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8080/api/v1/workflows `
  -ContentType application/json `
  -InFile examples/prompt-envelope.json
```

The local backend returns deterministic output and two canonical lifecycle events. It requires no Azure account.

## Foundry Next Gen Mode

The cloud adapter uses `AIProjectClient(...).get_openai_client().responses.create(...)` with an `agent_reference`. Configure only resource identifiers:

```text
ENVIRONMENT=dev
WORKFLOW_BACKEND=foundry
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_AGENT_NAME=<next-gen-agent-name>
```

In Azure, the application selects `ManagedIdentityCredential()` with no client ID, which binds to the Container App system-assigned identity. Grant that principal the minimum role needed at the Foundry project scope. Local development selects `DefaultAzureCredential()`.

## Container

```powershell
docker build --platform linux/amd64 -t cas-reference-product:local .
docker run --rm -p 8080:8080 cas-reference-product:local
```

The image runs as a non-root user, listens on port `8080`, and provides `/health/live` and `/health/ready`.

## Documentation

- [Architecture](docs/architecture.md)
- [Threat model](docs/threat-model.md)
- [Operations](docs/operations.md)
- [Immutable golden-path case-study evidence](docs/case-study-evidence.md)
- [cas-platform interface](deployment/cas-platform.interface.yaml)

## Security

Report vulnerabilities through GitHub private vulnerability reporting. Do not include credentials or sensitive prompt data in issues.
