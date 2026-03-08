# SSH into staging server (arved@tttc-staging-01).
# Usage: .\scripts\ssh-staging.ps1
# Override key: $env:TTTC_SSH_KEY = "C:\path\to\key"; .\scripts\ssh-staging.ps1

$Key = if ($env:TTTC_SSH_KEY) { $env:TTTC_SSH_KEY } else { Join-Path $env:USERPROFILE ".ssh\teufel_ed25519" }
$StagingHost = "46.225.208.231"
$User = "arved"

& ssh -i $Key "${User}@${StagingHost}" @args
