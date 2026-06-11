$ErrorActionPreference = 'Stop'

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path '.venv')) {
    Invoke-Checked { python -m venv .venv }
}

Invoke-Checked { & .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -e '.[dev]' }
Invoke-Checked { & .\.venv\Scripts\python.exe -m ruff check . }
Invoke-Checked { & .\.venv\Scripts\python.exe -m mypy }
Invoke-Checked { & .\.venv\Scripts\python.exe -m pytest }
Invoke-Checked { git -c safe.directory="$PWD" diff --check }
