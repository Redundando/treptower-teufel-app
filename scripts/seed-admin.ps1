#!/usr/bin/env pwsh
# Helper: seed the initial admin user (one-time) using the existing api/.venv
#
# WARNING: password is passed in plaintext via the command line.

param(
  [Parameter(Mandatory = $true)]
  [string] $email,

  [Parameter(Mandatory = $true)]
  [string] $password
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$ApiDir = Join-Path $RepoRoot "api"

$venvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Error "Missing $ApiDir\.venv. From api/: create venv and install deps first."
  exit 1
}

Set-Location $ApiDir
& $venvPython -m app.auth.seed_admin --email $email --password $password

