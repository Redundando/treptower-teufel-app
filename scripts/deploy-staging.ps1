# Deploy staging: push main, then either trigger GitHub Actions (-UseGitHub) or SSH deploy script.
# Prerequisite: server setup (docs/deploy.md). GitHub path needs secrets SSH_* + gh CLI auth.
# Usage:
#   .\scripts\deploy-staging.ps1
#   .\scripts\deploy-staging.ps1 -SkipPush
#   .\scripts\deploy-staging.ps1 -UseGitHub

param(
    [switch]$SkipPush,
    [switch]$UseGitHub
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

if (-not $SkipPush) {
    $status = git status --short
    if ($status) {
        Write-Host "You have uncommitted changes. Commit and push first, or use -SkipPush."
        exit 1
    }
    Write-Host "Pushing main..."
    git push origin main
}

if ($UseGitHub) {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) {
        Write-Error "Install GitHub CLI (gh) or run without -UseGitHub for SSH deploy."
        exit 1
    }
    Write-Host "Starting workflow 'Deploy staging'..."
    gh workflow run deploy-staging.yml
    Write-Host "Open Actions tab to watch the run. Ensure main on GitHub is the commit you want."
    exit 0
}

$Key = if ($env:TTTC_SSH_KEY) { $env:TTTC_SSH_KEY } else { Join-Path $env:USERPROFILE ".ssh\teufel_ed25519" }
$StagingHost = "46.225.208.231"
$User = "arved"

# Single remote argv: bash -lc "..." (PowerShell-safe quoting)
$RemoteCmd = 'bash -lc "set -e; if [ -d /srv/tttc/staging/repo ]; then cd /srv/tttc/staging/repo; elif [ -d /srv/tttc/app/repo ]; then cd /srv/tttc/app/repo; else echo No staging repo; exit 1; fi; exec bash scripts/deploy-remote-staging.sh"'

& ssh -i $Key "${User}@${StagingHost}" $RemoteCmd
