$ErrorActionPreference = 'Stop'
$env:ENVIRONMENT = 'local'
$env:WORKFLOW_BACKEND = 'local'

if (-not (Test-Path '.venv')) {
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -e '.[dev]'
}

& .\.venv\Scripts\python.exe -m uvicorn cas_reference_product.app:app --host 127.0.0.1 --port 8080

