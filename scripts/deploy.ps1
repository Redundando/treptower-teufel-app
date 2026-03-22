# Unified SSH deploy entry: staging or prod. Delegates to deploy-staging.ps1 / deploy-prod.ps1.
# See docs/deploy.md §4.
#
# Usage:
#   .\scripts\deploy.ps1 -DeployTo staging
#   .\scripts\deploy.ps1 -DeployTo staging -SkipPush
#   .\scripts\deploy.ps1 -DeployTo staging -UseGitHub
#   .\scripts\deploy.ps1 -DeployTo prod -Ref main
#   .\scripts\deploy.ps1 -DeployTo prod -Ref v0.1.2
#   .\scripts\deploy.ps1 -Env prod -Ref main   # -Env is alias for -DeployTo

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('staging', 'prod')]
    [Alias('Env')]
    [string]$DeployTo,

    [Parameter(Position = 1)]
    [string]$Ref = '',

    [switch]$SkipPush,
    [switch]$UseGitHub
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot

if ($DeployTo -eq 'staging') {
    if ($Ref) {
        Write-Warning '-Ref is ignored for staging (always deploys from server main).'
    }
    & "$ScriptDir\deploy-staging.ps1" -SkipPush:$SkipPush -UseGitHub:$UseGitHub
    exit $LASTEXITCODE
}

if ($SkipPush -or $UseGitHub) {
    Write-Error '-SkipPush and -UseGitHub apply only to staging. Use deploy-staging.ps1 directly.'
    exit 1
}

if ($Ref) {
    & "$ScriptDir\deploy-prod.ps1" $Ref
} else {
    & "$ScriptDir\deploy-prod.ps1"
}
exit $LASTEXITCODE
