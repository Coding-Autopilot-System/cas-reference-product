[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('dev', 'test', 'prod')]
    [string] $Environment,

    [string] $Location = 'northeurope',

    [string] $SubscriptionId
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$parameterFile = Join-Path $repoRoot "infra/parameters/$Environment.bicepparam"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI is required.'
}

if ($SubscriptionId) {
    az account set --subscription $SubscriptionId
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to select Azure subscription.'
    }
}

az account show --output none
if ($LASTEXITCODE -ne 0) {
    throw 'Authenticate with Azure CLI before running what-if.'
}

az deployment sub what-if `
    --name "cas-platform-$Environment-what-if" `
    --location $Location `
    --template-file (Join-Path $repoRoot 'infra/main.bicep') `
    --parameters $parameterFile `
    --no-pretty-print

if ($LASTEXITCODE -ne 0) {
    throw 'Azure what-if failed.'
}

