$ErrorActionPreference = 'Stop'

function Invoke-Checked {
    param([scriptblock]$Command)
    $global:LASTEXITCODE = 0
    & $Command
    if ($null -ne $global:LASTEXITCODE -and $global:LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $global:LASTEXITCODE"
    }
}

if (-not (Test-Path '.venv')) {
    Invoke-Checked { python -m venv .venv }
}

Invoke-Checked { & .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -e '.[dev]' }
Invoke-Checked { & .\.venv\Scripts\python.exe -m ruff check . }
Invoke-Checked { & .\.venv\Scripts\python.exe -m mypy }
Invoke-Checked { & .\.venv\Scripts\python.exe -m pytest }
Invoke-Checked { & .\.venv\Scripts\python.exe -m cas_reference_product.evidence }
$git = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $git -and (Test-Path 'C:\Program Files\Git\cmd\git.exe')) {
    $git = Get-Item 'C:\Program Files\Git\cmd\git.exe'
}
if ($null -eq $git) {
    throw 'Git executable was not found.'
}
$gitPath = if ($git.Source) { $git.Source } else { $git.FullName }
Invoke-Checked { & $gitPath -c safe.directory="$PWD" diff --check }
