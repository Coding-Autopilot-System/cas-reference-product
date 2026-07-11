# Operations

## Local run

```powershell
./scripts/validate.ps1
./scripts/run-local.ps1
```

Submit `examples/prompt-envelope.json` to `POST /api/v1/workflows`. Liveness is `/health/live`;
readiness is `/health/ready`.

Hardened local container run:

```powershell
docker run --rm --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges `
  -p 8080:8080 cas-reference-product:local
```

## CI gate (`.github/workflows/ci.yml`)

The `validate` job (Python 3.12, `pip install -e ".[dev]"`) runs on every push/PR to `main`:

```bash
python -m ruff check .
python -m mypy
python -m pytest tests/test_contract_registry.py -q --tb=short -o addopts=""
python -m pytest
python -m cas_reference_product.evidence
```

The contract-compatibility test is a consumer-side gate: it fails red if the pinned
`cas-contracts` version or the vendored v0.1 schema release drifts from what the Pydantic
models emit.

The `docker` job builds a Linux/amd64 image, runs it locally with `ENVIRONMENT=local` and
`WORKFLOW_BACKEND=local`, health-checks `/health/live` and `/health/ready`, and — only on push
to `main` — pushes to GHCR. There is no coverage-percentage gate in this repo's CI as of this
writing; the gate is ruff/mypy/pytest/evidence pass-fail, not a coverage threshold.

## Foundry mode

Set `ENVIRONMENT` to `dev`/`test`/`prod`, `WORKFLOW_BACKEND=foundry`, and the non-secret
`FOUNDRY_PROJECT_ENDPOINT`/`FOUNDRY_AGENT_NAME`. The Azure-hosted workload uses its
system-assigned managed identity; no API keys or client secrets are configured. Readiness fails
until required Foundry identifiers are present; Foundry connectivity is exercised only by
workflow requests, not probes.

## Platform handoff (validation only, no deploy)

```powershell
az bicep build --file infra/main.bicep
az deployment group what-if --resource-group <resource-group> --template-file infra/main.bicep --parameters foundryProjectResourceId=<resource-id>
```

Deployment is intentionally not performed by repository validation — consistent with the
workspace NO-AZURE-deploy lock. Build a Linux AMD64 image and pass its immutable image reference
to the `containerImage` parameter of `cas-platform`; review
`deployment/cas-platform.interface.yaml` before platform changes.

<!-- docs-verified: 57c21b03a48332728105b72a90e8e89deda409af 2026-07-08 -->
