$ErrorActionPreference = 'Stop'

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'Run ./scripts/validate.ps1 first to create the development environment.'
}

& .\.venv\Scripts\python.exe -m cas_reference_product.evidence
if ($LASTEXITCODE -ne 0) {
    throw "Evidence verification failed with exit code $LASTEXITCODE"
}
