# Threat Model

## Assets

- Prompt content and workflow results
- CAS lifecycle metadata and traces
- Foundry project and agent
- Container App system-assigned identity

## Trust Boundaries

- Caller to public API
- Application to Foundry project endpoint
- Application telemetry to Azure Monitor
- CI to public package and container registries

## Threats and Controls

| Threat | Control | Residual risk |
|--------|---------|---------------|
| Credential disclosure | No keys or tokens in code; system-assigned `ManagedIdentityCredential` in Azure | Operators must maintain least-privilege RBAC |
| Legacy API use | Adapter uses project Responses client with `agent_reference`; no Classic Assistants code | SDK behavior must be reviewed during upgrades |
| Prompt injection | Workflow treats prompts as untrusted data and exposes no tools in v0.1 | Downstream agent policy remains product-specific |
| Sensitive telemetry | Events contain identifiers and status, not prompt text or agent output | Operators must review SDK and platform log settings |
| Unauthorized invocation | External ingress disabled by default in platform interface | Authentication gateway is product-specific and out of scope |
| Supply-chain compromise | Pinned CI actions, lint, tests, non-root container | Dependency update review remains required |
| Denial of service | Platform scaling bounds and request validation | Product-specific quotas and rate limits are not included |

## Required RBAC

Grant the Container App system-assigned identity only the minimum Foundry project role needed to invoke the selected agent, scoped to the narrowest resource. Do not assign subscription-wide roles.

