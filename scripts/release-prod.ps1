# Create semver tag and push → triggers GitHub Actions prod deploy.
# Usage: .\scripts\release-prod.ps1 0.1.0
#        .\scripts\release-prod.ps1 v1.2.3
# Requires: clean working tree, commit on main you want in prod; prod server provisioned.

param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

$ver = $Version.Trim() -replace '^v', ''
if ($ver -notmatch '^\d+\.\d+\.\d+') {
    Write-Error "Version must be semver, e.g. 0.1.0 or v1.2.3"
    exit 1
}
$tag = "v$ver"

$status = git status --short
if ($status) {
    Write-Error "Working tree not clean. Commit or stash before releasing."
    exit 1
}

$existing = git tag -l $tag
if ($existing) {
    Write-Error "Tag $tag already exists."
    exit 1
}

Write-Host "Tagging $tag at $(git rev-parse --short HEAD)..."
git tag $tag
Write-Host "Pushing tag (triggers prod deploy workflow)..."
git push origin $tag
$origin = git remote get-url origin
if ($origin -match 'github\.com[:/]([^/]+)/([^/.]+)') {
    Write-Host "Done. Actions: https://github.com/$($matches[1])/$($matches[2])/actions"
} else {
    Write-Host "Done. Check GitHub Actions for the prod workflow."
}
