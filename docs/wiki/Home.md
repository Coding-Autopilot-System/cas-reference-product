# cas-reference-product Wiki

`cas-reference-product` is the public v0.1 reference application for the Coding Autopilot
System and Microsoft Foundry Next Gen Agents. It runs a deterministic workflow locally, emits
canonical `cas-contracts` v0.1 lifecycle events, and includes a Foundry adapter that invokes a
Next Gen agent through the project Responses client. It is designed for the Container Apps and
managed-identity boundary supplied by `cas-platform`.

## Deployment status: local-first, no live Azure deploy

This project does not use Classic Assistants APIs and does not deploy Azure resources. See
[Architecture](Architecture.md) for the full NO-AZURE-deploy-lock statement.

## Quickstart

```powershell
./scripts/validate.ps1
./scripts/run-local.ps1
```

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8080/api/v1/workflows `
  -ContentType application/json `
  -InFile examples/prompt-envelope.json
```

The local backend returns deterministic output and two canonical lifecycle events. It requires
no Azure account.

## Where to go next

- [Architecture](Architecture.md) — request flow, local vs. Foundry adapters, deploy-lock posture
- [Operations](Operations.md) — verified run/test/CI commands
- [Decisions](Decisions.md) — index of recorded architectural decisions

<!-- docs-verified: 57c21b03a48332728105b72a90e8e89deda409af 2026-07-08 -->
