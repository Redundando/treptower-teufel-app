# Start the FastAPI dev server from the repo root (loads root .env via --app-dir api).
# Prerequisite: api\.venv exists and deps installed (pip install -e . in api/).
# Usage:
#   .\scripts\run-api.ps1
#   .\scripts\run-api.ps1 --port 8001

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

$venvPython = Join-Path $RepoRoot "api\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Missing api\.venv. From api\: python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e ."
    exit 1
}

& $venvPython -m uvicorn app.main:app --reload --app-dir api @args
