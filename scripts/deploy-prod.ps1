# Deploy production over SSH: runs scripts/deploy-remote-prod.sh on the server.
# Same steps as GitHub Actions "Deploy production" (checkout tag, sync api/web, pip, npm, migrate, restart).
#
# Usage:
#   .\scripts\deploy-prod.ps1 v0.1.2     # deploy that tag (must exist on origin)
#   .\scripts\deploy-prod.ps1            # fetch tags, deploy latest local v*.*.* tag
#
# Prerequisite: /srv/tttc/prod on server, venv + env files; see docs/deploy.md.

param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$GitRef
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

if ([string]::IsNullOrWhiteSpace($GitRef)) {
    Write-Host "Fetching tags from origin..."
    git fetch origin --tags
    $latest = git tag -l --sort=-v:refname | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
    if (-not $latest) {
        Write-Error "No v*.*.* tag found locally. Pass a tag: .\scripts\deploy-prod.ps1 v0.1.0"
        exit 1
    }
    $GitRef = $latest
    Write-Host "Using latest semver tag: $GitRef"
}

$Key = if ($env:TTTC_SSH_KEY) { $env:TTTC_SSH_KEY } else { Join-Path $env:USERPROFILE ".ssh\teufel_ed25519" }
$ServerHost = "46.225.208.231"
$User = "arved"

Write-Host "Deploying prod GIT_REF=$GitRef via SSH..."
# Single argv for ssh; bash expands GIT_REF on the server (semver tags need no quoting).
& ssh -i $Key "${User}@${ServerHost}" "bash -lc 'set -euo pipefail; cd /srv/tttc/prod/repo; export GIT_REF=$GitRef; exec bash scripts/deploy-remote-prod.sh'"
