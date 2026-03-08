# Add all changes, commit with message, push to origin main.
# Usage: .\scripts\commit-and-push.ps1 "Your commit message"
# Or from repo root: .\scripts\commit-and-push.ps1 -Message "Your commit message"

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Message
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

git add -A
$status = git status --short
if (-not $status) {
    Write-Host "Nothing to commit (working tree clean)."
    exit 0
}
git commit -m "$Message"
git push origin main
Write-Host "Done: added, committed, pushed to main."
