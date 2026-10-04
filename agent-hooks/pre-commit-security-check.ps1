# Lightweight security check before commit (no network, no AWS).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Pre-commit security check" -ForegroundColor Cyan

if (Test-Path ".env") {
    $envTracked = git ls-files --error-unmatch .env 2>$null
    if ($LASTEXITCODE -eq 0) {
        throw ".env is tracked by git — remove it and use .env.example only."
    }
}

$forbiddenNames = @(".env", "credentials.json", "*.pem", "id_rsa")
foreach ($name in $forbiddenNames) {
    $staged = git diff --cached --name-only -- $name
    if ($staged) {
        throw "Attempting to commit sensitive file pattern: $name"
    }
}

$diff = git diff --cached -U0
if ($diff -match 'GROQ_API_KEY\s*=\s*[^\s#]+' -and $diff -notmatch 'GROQ_API_KEY=\s*$') {
    throw "Staged diff may contain a GROQ_API_KEY value."
}

Write-Host "No obvious secret staging issues."

Write-Host "==> ruff (backend)"
Push-Location backend
try { ruff check . } finally { Pop-Location }

Write-Host "Pre-commit security check passed." -ForegroundColor Green
