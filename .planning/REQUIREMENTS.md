# Requirements: CAS Reference Product

**Defined:** 2026-06-11
**Core Value:** Run and inspect one complete, traceable CAS workflow locally and deploy the same container through `cas-platform`.

## v0.1 Requirements

- [x] **API-01**: Caller can submit a prompt envelope and receive a workflow result.
- [x] **AGENT-01**: Application supports a Foundry Next Gen agent-reference adapter and a local deterministic adapter.
- [x] **ID-01**: Azure-hosted mode uses system-assigned managed identity and code contains no credentials.
- [x] **CONTRACT-01**: Application emits canonical `PromptEnvelope` and `RunEvent` v0.1 records.
- [x] **OBS-01**: HTTP, workflow, and Foundry boundaries create OpenTelemetry spans and support Application Insights export.
- [x] **OPS-01**: Application exposes liveness and readiness probes.
- [x] **PLAT-01**: Container interface matches `cas-platform` port and environment model.
- [x] **QUAL-01**: Unit, API, contract, static, and container configuration checks run in CI.
- [x] **DOC-01**: Architecture, threat model, operations, and local workflow are documented.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Azure deployment | Explicitly prohibited for v0.1 |
| Classic Assistants integration | Foundry Next Gen only |
| Durable workflow storage | Requires product-specific persistence design |

## Traceability

All v0.1 requirements map to Phase 1 and are complete.

---
*Last updated: 2026-06-11 after v0.1 implementation*

