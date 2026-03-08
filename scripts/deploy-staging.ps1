# Deploy to staging: push local main, then SSH to server and run the remote deploy script.
# Prerequisite: First-time setup (clone, env, firewall) done once on the server (see docs/deploy.md).
# Usage: .\scripts\deploy-staging.ps1
# Optional: .\scripts\deploy-staging.ps1 -SkipPush   (to only run remote steps, e.g. after pushing yourself)

param(
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

if (-not $SkipPush) {
    $status = git status --short
    if ($status) {
        Write-Host "You have uncommitted changes. Commit and push first, or use -SkipPush to only run on server."
        exit 1
    }
    Write-Host "Pushing main..."
    git push origin main
}

$Key = if ($env:TTTC_SSH_KEY) { $env:TTTC_SSH_KEY } else { Join-Path $env:USERPROFILE ".ssh\teufel_ed25519" }
$StagingHost = "46.225.208.231"
$User = "arved"

$RemoteCmd = "cd /srv/tttc/app/repo && git pull origin main && bash scripts/staging-deploy-remote.sh"
& ssh -i $Key "${User}@${StagingHost}" $RemoteCmd
