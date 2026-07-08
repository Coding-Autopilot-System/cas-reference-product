# Roadmap: CAS Reference Product

## Phase 1: Public v0.1 Reference Application

**Goal:** Deliver a locally runnable, cloud-ready reference workload without deploying Azure resources.

**Requirements:** API-01, AGENT-01, ID-01, CONTRACT-01, OBS-01, OPS-01, PLAT-01, QUAL-01, DOC-01

**Success criteria:**
- Local workflow request succeeds and returns canonical events.
- Tests, lint, type checks, and Docker build pass.
- Foundry mode uses Next Gen agent references and managed identity.
- Public documentation states deployment and security boundaries.

Status: Complete

## Phase 2: Telemetry Hardening

**Goal:** Wire OpenTelemetry end-to-end with lifecycle span events, W3C trace propagation, and Application Insights exporter.

**Requirements:** TEL-01, TEL-02, TEL-03, TEL-04

**Success criteria:**
- Every /api/v1/workflows request creates a `cas.api.workflows.execute` span with correlation_id, run_id, and intent attributes.
- Span events `workflow.started`, `workflow.completed`, and `workflow.failed` are emitted at the appropriate lifecycle points.
- W3C traceparent/tracestate headers on inbound requests are extracted and linked as parent context.
- Application Insights exporter activates when APPLICATIONINSIGHTS_CONNECTION_STRING is set; no-op otherwise.
- All telemetry behaviours verified by pytest with InMemorySpanExporter.

Status: Complete

## Phase 3: Docker + CI Publish

**Goal:** Containerize the app with a production-grade multi-stage Dockerfile and publish the image to GHCR on merge to main.

**Requirements:** DOCK-01, DOCK-02, DOCK-03

**Success criteria:**
- Multi-stage Dockerfile builds a linux/amd64 image, runs as non-root `appuser`, exposes port 8080, and health-checks via /health/ready.
- docker-compose.yml starts the local dev stack with env stubs using .env.example.
- CI docker job builds, smoke-tests (/health/live + /health/ready), and on push to main pushes to ghcr.io/coding-autopilot-system/cas-reference-product.

Status: Complete
