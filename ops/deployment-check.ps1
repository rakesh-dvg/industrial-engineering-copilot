# Local deployment smoke check (no AWS).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> docker compose ps"
docker compose ps

$base = $env:IEC_API_BASE
if (-not $base) { $base = "http://localhost:8020" }

Write-Host "==> GET $base/health"
try {
    $response = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 5
    $response | ConvertTo-Json -Depth 4
} catch {
    Write-Warning "Backend not reachable at $base — start uvicorn or docker compose backend."
    exit 1
}

Write-Host "Deployment smoke check OK." -ForegroundColor Green
