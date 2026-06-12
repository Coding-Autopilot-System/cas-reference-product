# Operations

## Local

```powershell
./scripts/validate.ps1
./scripts/run-local.ps1
```

Submit `examples/prompt-envelope.json` to `POST /api/v1/workflows`. Liveness is `/health/live`; readiness is `/health/ready`.

## Foundry Mode

Set `ENVIRONMENT` to `dev`, `test`, or `prod`; set `WORKFLOW_BACKEND=foundry`; provide the non-secret `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_AGENT_NAME`. The Azure-hosted workload uses its system-assigned managed identity. Do not configure API keys or client secrets.

Readiness fails until required Foundry identifiers are present. Foundry connectivity is exercised only by workflow requests, not probes.

When `APPLICATIONINSIGHTS_CONNECTION_STRING` is supplied, telemetry export also authenticates with
the environment credential. Grant the system-assigned identity the minimum Azure Monitor publishing
role required by the deployment. Retry-file storage and broad outbound HTTP/SDK auto-instrumentation
are disabled; explicit spans do not record prompt or output content.

## Platform Handoff

Build a Linux AMD64 image and pass its immutable image reference to the `containerImage` parameter of `cas-platform`. Review `deployment/cas-platform.interface.yaml` before platform changes. This repository intentionally contains no Azure deployment command.
