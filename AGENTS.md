# Repository Instructions

This repository is the public CAS reference product.

- Use Foundry Next Gen Agents through the project Responses client. Do not use Classic Assistants APIs.
- Use `ManagedIdentityCredential` in Azure and `DefaultAzureCredential` only for local development.
- Never commit secrets, keys, tokens, or real connection strings.
- Preserve the canonical `cas-contracts` v0.1 lifecycle event shapes.
- Do not deploy Azure resources from this repository.
- Run `./scripts/validate.ps1` before committing.

