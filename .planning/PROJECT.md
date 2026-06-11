# CAS Reference Product

## What This Is

A public, production-oriented reference application showing how a CAS workload integrates with Microsoft Foundry Next Gen Agents while running on the `cas-platform` Container Apps foundation. It demonstrates canonical lifecycle events, managed identity, observability boundaries, probes, tests, and a safe local workflow without provisioning Azure resources.

## Core Value

Developers can run and inspect one complete, traceable CAS workflow locally, then deploy the same container through the `cas-platform` interface without changing its security model.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Expose a useful workflow API with local and Foundry Next Gen modes.
- [ ] Emit canonical `cas-contracts` v0.1 lifecycle records with W3C trace context.
- [ ] Use system-assigned managed identity in Azure and no embedded secrets.
- [ ] Define OpenTelemetry and Application Insights boundaries.
- [ ] Provide health, readiness, tests, Docker, CI, architecture, threat model, and local workflow.
- [ ] Match the workload interface expected by `cas-platform`.

### Out of Scope

- Azure resource deployment - explicitly prohibited for v0.1.
- Classic Assistants APIs - violate the Foundry Next Gen mandate.
- Production authorization and persistence - require product-specific policy and data design.

## Context

`cas-contracts` v0.1 is the authoritative lifecycle contract. `cas-platform` hosts a port-8080 container with a system-assigned managed identity and workspace observability. The application must remain useful without Azure access, while making the cloud integration explicit and testable.

## Constraints

- **Identity**: Managed identity only in Azure; no embedded credentials.
- **Platform**: Linux AMD64 container listening on port 8080.
- **Cloud safety**: No Azure deployment or resource mutation.
- **Public repository**: Examples and defaults contain no sensitive data.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python, FastAPI, and Pydantic | Compact public reference with strong contracts and testability | Pending |
| Local deterministic adapter by default | CI and contributors can run without Azure | Pending |
| Foundry project Responses client with agent reference | Demonstrates Next Gen Agent invocation without Classic Assistants | Pending |
| Production uses `ManagedIdentityCredential` | Deterministic system-assigned identity boundary | Pending |

## Evolution

Review requirements, decisions, and scope at each phase transition and milestone.

---
*Last updated: 2026-06-11 after initialization*

