# Create semver tag and push → triggers GitHub Actions prod deploy.
# Usage:
#   .\scripts\release-prod.ps1                    # git fetch, then next patch from latest v*.*.* tag
#   .\scripts\release-prod.ps1 0.1.0              # explicit version (same as v0.1.0)
#   .\scripts\release-prod.ps1 -SkipFetch         # skip git fetch (offline / tags already current)
# Requires: clean working tree; prod server provisioned. See docs/github-actions.md.

param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$Version,
    [switch]$SkipFetch
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

function Get-NextPatchTag {
    $latest = git tag -l --sort=-v:refname | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
    if (-not $latest) {
        return "v0.1.0"
    }
    $parts = $latest.TrimStart('v') -split '\.'
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2] + 1
    return "v$major.$minor.$patch"
}

if (-not $SkipFetch) {
    Write-Host "Fetching from origin (tags)..."
    git fetch origin
}

$status = git status --short
if ($status) {
    Write-Error "Working tree not clean. Commit or stash before releasing."
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $tag = Get-NextPatchTag
    Write-Host "No version passed — using next patch: $tag"
} else {
    $ver = $Version.Trim() -replace '^v', ''
    if ($ver -notmatch '^\d+\.\d+\.\d+') {
        Write-Error "Version must be semver, e.g. 0.1.0 or v1.2.3"
        exit 1
    }
    $tag = "v$ver"
}

$existing = git tag -l $tag
if ($existing) {
    Write-Error "Tag $tag already exists (after fetch). Pick another version or delete the tag if it was a mistake."
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
