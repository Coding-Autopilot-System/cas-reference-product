# Architecture

```text
Caller
  -> FastAPI boundary (:8080)
     -> PromptEnvelope validation (cas-contracts v0.1)
     -> WorkflowOrchestrator
        -> LocalWorkflowAgentService (default)
        -> FoundryWorkflowAgentService (configured)
           -> AIProjectClient project Responses client
           -> Next Gen agent_reference
     -> canonical RunEvent records
     -> OpenTelemetry spans
        -> Application Insights when deployment injects configuration
```

The application owns workflow orchestration and lifecycle records. Foundry owns agent execution. `cas-platform` owns Container Apps, system-assigned identity, diagnostic settings, Log Analytics, and Application Insights resources.

Foundry mode uses `ManagedIdentityCredential()` for every non-local environment. Local mode uses `DefaultAzureCredential()` only for developer convenience. No Classic Assistants API is used.

The Foundry call is isolated behind the `WorkflowAgentService` protocol. This keeps core lifecycle behavior deterministic and testable while making the external service boundary explicit.

## Deployment Interface

`deployment/cas-platform.interface.yaml` records the contract: Linux AMD64 image, port 8080, internal ingress by default, system-assigned identity, probes, non-secret identifiers, and platform outputs. It does not deploy resources.

## Observability Boundaries

- Incoming HTTP requests are instrumented by Azure Monitor OpenTelemetry when configured.
- `cas.workflow.execute` covers core orchestration.
- `foundry.responses.create` covers the external Foundry call.
- CAS correlation IDs are attached to workflow spans and canonical events preserve W3C trace context.

