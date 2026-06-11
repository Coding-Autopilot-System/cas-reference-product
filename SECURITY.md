# Security Policy

## Reporting

Report vulnerabilities through GitHub private vulnerability reporting. Do not open public issues containing credentials, tokens, sensitive prompts, customer data, or exploit details.

## Security Baseline

- Azure-hosted execution uses system-assigned managed identity.
- The repository accepts no credentials, keys, or tokens.
- Foundry integration uses Next Gen agent references, not Classic Assistants.
- External ingress is disabled by default in the platform interface.
- The container runs as a non-root user.

Azure resources are not deployed from this repository.

