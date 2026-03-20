#!/usr/bin/env pwsh
#
# Behavior:
# 1) If anything is listening on the target ports, kill it.
# 2) Start FastAPI + Vite.
# 3) Print URLs and exit ("Done").
#
# Requirements:
# - api/.venv exists
# - web/node_modules exists (or npm will fail)

param(
  [int] $ApiPort = 8000,
  [int] $WebPort = 5173
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$ApiDir = Join-Path $RepoRoot "api"
$WebDir = Join-Path $RepoRoot "web"
$VenvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
  throw "Missing api/.venv. Run: cd api; python -m venv .venv"
}

$npmCmdAll = Get-Command npm -All -ErrorAction SilentlyContinue
if (-not $npmCmdAll) {
  throw "Could not find `npm` on PATH. Run: npm --version"
}

# On Windows, `Get-Command npm` may resolve to `npm.ps1` (script) or `npm.cmd` (batch).
# `Start-Process` works reliably with an actual executable/batch entrypoint, so prefer `npm.cmd`.
$npmExe = ($npmCmdAll | Where-Object { $_.CommandType -eq "Application" -and $_.Path -match "\\npm\\.cmd$" } | Select-Object -First 1).Path
if (-not $npmExe) {
  $npmExe = ($npmCmdAll | Where-Object { $_.CommandType -eq "Application" } | Select-Object -First 1).Path
}
if (-not $npmExe) {
  throw "Resolved `npm` to an unsupported entrypoint. Run: Get-Command npm -All"
}

function Stop-ListenerOnPort([int] $port) {
  $conns = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
  if ($conns.Count -eq 0) { return }

  $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($procId in $pids) {
    try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch { }
  }
}

Write-Host "Killing anything on ports: API=$ApiPort, Web=$WebPort"
Stop-ListenerOnPort $ApiPort
Stop-ListenerOnPort $WebPort

$apiOutLog = Join-Path $RepoRoot "logs\dev-start-all-api.out.log"
$apiErrLog = Join-Path $RepoRoot "logs\dev-start-all-api.err.log"
$webOutLog = Join-Path $RepoRoot "logs\dev-start-all-web.out.log"
$webErrLog = Join-Path $RepoRoot "logs\dev-start-all-web.err.log"
New-Item -ItemType Directory -Path (Join-Path $RepoRoot "logs") -Force | Out-Null

# `Start-Process -RedirectStandardInput` expects a real file path (not `NUL`).
# Use an empty temp file so child processes can't consume your terminal keystrokes.
$stdinNullFile = Join-Path $RepoRoot "logs\dev-stdin-null.txt"
"" | Out-File -FilePath $stdinNullFile -Encoding ascii -Force

Write-Host "Starting API ..."
Start-Process -FilePath $VenvPython `
  -WorkingDirectory $RepoRoot `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--app-dir", "api", "--port", $ApiPort `
  -RedirectStandardOutput $apiOutLog -RedirectStandardError $apiErrLog -RedirectStandardInput $stdinNullFile -WindowStyle Hidden | Out-Null

Write-Host "Starting frontend ..."
$portArgs = @(
  "run", "dev",
  "--",
  "--port", $WebPort,
  "--host", "127.0.0.1"
)
Start-Process -FilePath $npmExe `
  -WorkingDirectory $WebDir `
  -ArgumentList $portArgs `
  -RedirectStandardOutput $webOutLog -RedirectStandardError $webErrLog -RedirectStandardInput $stdinNullFile -WindowStyle Hidden | Out-Null

function Test-LocalPort([int] $port, [int] $timeoutSeconds) {
  $client = $null
  try {
    # Avoid `Test-NetConnection -TimeoutSeconds` because it isn't available in older Windows PowerShell versions.
    $client = New-Object System.Net.Sockets.TcpClient
    $task = $client.ConnectAsync("127.0.0.1", $port)
    $ok = $task.Wait([TimeSpan]::FromSeconds($timeoutSeconds))
    if (-not $ok) { return $false }
    return $client.Connected
  } catch {
    return $false
  } finally {
    try { if ($client) { $client.Dispose() } } catch { }
  }
}

Write-Host "Waiting for services to bind ports ..."
$apiUp = $false
$webUp = $false
for ($i = 0; $i -lt 20; $i++) {
  if (-not $apiUp) { $apiUp = Test-LocalPort $ApiPort 1 }
  if (-not $webUp) { $webUp = Test-LocalPort $WebPort 1 }
  if ($apiUp -and $webUp) { break }
  Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "API: http://127.0.0.1:$ApiPort (up=$apiUp)"
Write-Host "Web: http://localhost:$WebPort (up=$webUp)"
Write-Host "Logs: $apiOutLog , $apiErrLog , $webOutLog , $webErrLog"
Write-Host "Done."

