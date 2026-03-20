#!/usr/bin/env pwsh
# Helper: run PostgreSQL migrations using the existing api/.venv

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$ApiDir = Join-Path $RepoRoot "api"

$venvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Missing $ApiDir\.venv. From api/: create venv and install deps first."
    Write-Error "Example: python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e ."
    exit 1
}

Set-Location $ApiDir
& $venvPython -m app.db.migrate @args

