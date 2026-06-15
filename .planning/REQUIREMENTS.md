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

## Phase 2 Requirements — Telemetry Hardening

- [x] **TEL-01**: OpenTelemetry SDK wired into FastAPI lifespan — a `cas.api.workflows.execute` span is created for every /api/v1/workflows request, carrying `cas.correlation_id`, `cas.run_id`, and `cas.intent` attributes.
- [x] **TEL-02**: Canonical CAS lifecycle events emitted as span events: `workflow.started` (with correlation_id + run_id), `workflow.completed` on success, `workflow.failed` on error — never both completed and failed.
- [x] **TEL-03**: W3C trace context headers (`traceparent` / `tracestate`) propagated on inbound requests via `W3CTraceContextMiddleware`; downstream spans are parented to the caller's trace.
- [x] **TEL-04**: Application Insights exporter active when `APPLICATIONINSIGHTS_CONNECTION_STRING` env var is set (no-op if absent); uses managed identity and privacy-hardened instrumentation options.

## Phase 3 Requirements — Docker + CI Publish

- [x] **DOCK-01**: Dockerfile is multi-stage (builder + runtime), targets linux/amd64, exposes port 8080, runs as non-root user `appuser`, and health-checks via /health/ready.
- [x] **DOCK-02**: `docker-compose.yml` defines a local dev stack (`cas-ref` service, ports 8080:8080, env_file .env.example) that starts without Azure credentials.
- [x] **DOCK-03**: CI pipeline (`docker` job in ci.yml) builds the image, runs a health-check smoke test, and pushes to `ghcr.io/coding-autopilot-system/cas-reference-product` on merge to main.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Azure deployment | Explicitly prohibited for v0.1 |
| Classic Assistants integration | Foundry Next Gen only |
| Durable workflow storage | Requires product-specific persistence design |

## Traceability

All v0.1 requirements map to Phase 1 and are complete.
TEL-01 through TEL-04 map to Phase 2 and are complete.
DOCK-01 through DOCK-03 map to Phase 3 and are complete.

---
*Last updated: 2026-06-14 after Phase 2 and Phase 3 implementation*
