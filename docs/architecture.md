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

`deployment/cas-platform.interface.yaml` records the application contract: Linux AMD64 image, port
8080, internal ingress by default, system-assigned identity, probes, and configuration inputs. It does
not deploy resources.

The application consumes only the environment values listed in that interface. Platform resource IDs
and principal IDs remain deployment-orchestration outputs and are not application configuration.

## Observability Boundaries

- Incoming HTTP requests are instrumented by Azure Monitor OpenTelemetry when configured.
- `cas.workflow.execute` covers core orchestration.
- `foundry.responses.create` covers the external Foundry call.
- CAS correlation IDs are attached to workflow spans and canonical events preserve W3C trace context.
- Broad Azure SDK and outbound HTTP auto-instrumentation is disabled to avoid capturing prompt or
  output content. The application records only explicit boundary spans and safe identifiers.
# Loop execution boundaries

The public HTTP ingress is an Azure Functions Flex Consumption Linux app. It validates the canonical prompt envelope and returns `202` only after handing the message to Azure Queue Storage. It never invokes Foundry, executes tools, or runs sandbox work in the request process. A separately scaled worker owns those long-running operations.

The ingress uses a system-assigned managed identity. Bicep grants Storage Queue Data Contributor on the workload storage account and Azure AI User on the specific Foundry project. No account keys, API keys, or connection-string credentials are materialized. Local development continues to use `DefaultAzureCredential`; Azure environments use `ManagedIdentityCredential`.

Loop spans use W3C trace context and the fixed stages `control_plane`, `worker`, `tool`, `verifier`, and `foundry`. Attributes are limited to correlation, goal, and work-item identifiers; prompts and model output are not telemetry attributes.
