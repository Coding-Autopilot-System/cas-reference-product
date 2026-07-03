# CAS Reference Product Documentation

Welcome to the **CAS Reference Product** developer documentation.

## Overview

The CAS Reference Product is a public v0.1 reference application designed for the **Coding Autopilot System (CAS)** and **Microsoft Foundry Next Gen Agents**. It demonstrates how to integrate with the Foundry platform while adhering to canonical `cas-contracts` lifecycle events.

Key features include:
- **FastAPI Web Service**: Serves the application boundary via `/api/v1/workflows`.
- **Foundry Next Gen Integration**: Connects seamlessly with Azure AI Projects using `WorkflowAgentService`.
- **Identity & Security**: Relies entirely on system-assigned Managed Identity; there are no embedded secrets.
- **Canonical Lifecycle Events**: Strongly typed data models for input (`PromptEnvelope`) and output (`RunEvent`).
- **Telemetry**: Full OpenTelemetry tracing including W3C trace context middleware.

## Getting Started

To run the application locally without Azure:

```powershell
./scripts/validate.ps1
./scripts/run-local.ps1
```

Once running, send a POST request to `http://127.0.0.1:8080/api/v1/workflows` with a valid `PromptEnvelope` payload.

## Structure

- **src/cas_reference_product/app.py**: FastAPI application setup, middleware, and routing.
- **src/cas_reference_product/workflow.py**: Workflow orchestrator and implementations for local and Foundry backends.
- **src/cas_reference_product/models.py**: Pydantic models for canonical events.
- **src/cas_reference_product/identity.py**: Azure Identity credential configuration.
- **src/cas_reference_product/telemetry.py**: OpenTelemetry and W3C trace context integration.

## Documentation Index

- [Architecture Details](architecture.md)
- [Threat Model](threat-model.md)
- [Operations Guide](operations.md)
- [Case Study Evidence](case-study-evidence.md)
