# cas-reference-product

Production-oriented CAS reference application demonstrating a complete workload integrated with **Microsoft Foundry Next Gen Agents** on a Container Apps foundation. Runs locally without Azure, deploys unmodified through the `cas-platform` interface.

## Project Context

See `.planning/PROJECT.md` for goals and requirements. This project is in early initialization.

**Core mandate**: Demonstrate canonical CAS lifecycle events, managed identity, observability, probes, and a safe local workflow — without embedding any Azure credentials.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| API framework | FastAPI + Pydantic |
| Azure identity | `ManagedIdentityCredential` (system-assigned; no embedded secrets) |
| Azure AI | Foundry Next Gen Agents (`WorkflowAgentService`) — never Classic Assistants |
| Observability | OpenTelemetry + Azure Application Insights |
| Container | Linux AMD64, port 8080 |
| Tests | pytest (in `tests/`) |
| Local dev | `scripts/run-local.ps1` |

## Key Files

| File | Purpose |
|---|---|
| `src/cas_reference_product/identity.py` | Identity/credential resolution (local vs. managed) |
| `.foundry/agent-metadata.yaml` | Foundry Next Gen Agent configuration |
| `.foundry/datasets/` | Seed data for local testing |
| `.env.example` | All required environment variable docs |
| `scripts/run-local.ps1` | Local run without Azure |

## Local Development

```powershell
.\scripts\run-local.ps1
```

Or manually:
```bash
cd portfolio/cas-reference-product
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # if present, else pip install -e .
python -m pytest tests/
```

## Constraints

- **No embedded credentials** — use `DefaultAzureCredential` / `ManagedIdentityCredential` only
- **No Azure resource deployment** — local adapter runs without provisioning
- **Foundry Next Gen only** — reject any Classic Assistants (`asst_*`) usage
- **Public repo** — no sensitive data in examples or defaults

## GSD Workflow

Use `/gsd:plan-phase` before any multi-file change. Use `/gsd:quick` for single-file fixes.
