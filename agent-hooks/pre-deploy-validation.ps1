# Pre-deploy validation hook — local checks only (no AWS deployment).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Pre-deploy validation (local)" -ForegroundColor Cyan

$required = @(
    "openapi.yaml",
    "docker-compose.yml",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "frontend/nginx.conf.template",
    ".env.example"
)
foreach ($path in $required) {
    if (-not (Test-Path $path)) {
        throw "Missing required file: $path"
    }
}

Write-Host "Required files present."

Write-Host "==> docker compose config"
docker compose config | Out-Null

Write-Host "==> OpenAPI path check"
python .github/scripts/check_openapi_paths.py

Write-Host "==> Secret pattern scan (staged + tracked text)"
$patterns = @(
    'gsk_[A-Za-z0-9]{20,}',
    'AKIA[0-9A-Z]{16}',
    'BEGIN (RSA |OPENSSH )?PRIVATE KEY'
)
$hits = @()
foreach ($pattern in $patterns) {
    $matches = git grep -n -E $pattern -- ':!*.md' ':!security/*' ':!.env.example' 2>$null
    if ($matches) { $hits += $matches }
}
if ($hits.Count -gt 0) {
    Write-Host "Possible secrets detected in tracked files:" -ForegroundColor Red
    $hits | ForEach-Object { Write-Host $_ }
    throw "Resolve secret-like patterns before deploy."
}

Write-Host "==> Backend tests (quick subset)"
Push-Location backend
try {
    if (-not $env:TEST_DATABASE_URL) {
        $env:TEST_DATABASE_URL = "postgresql+asyncpg://iec:iec@localhost:5432/iec"
    }
    pytest -q tests/test_health.py tests/test_architecture_invariants.py
} finally {
    Pop-Location
}

Write-Host "Pre-deploy validation passed." -ForegroundColor Green
