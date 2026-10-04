# Reset the LOCAL demo database and re-seed deterministic demo data.
# WARNING: This deletes Docker volumes (PostgreSQL + MinIO data).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "WARNING: This will delete local PostgreSQL and MinIO Docker volumes." -ForegroundColor Red
$confirm = Read-Host "Type RESET to continue"
if ($confirm -ne "RESET") {
    Write-Host "Aborted."
    exit 1
}

Push-Location $Root
Write-Host "Stopping containers and removing volumes..." -ForegroundColor Cyan
docker compose down -v
docker compose up -d postgres redis minio
Pop-Location

Start-Sleep -Seconds 8

Push-Location (Join-Path $Root "backend")
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]" | Out-Null

Write-Host "Running migrations and seeds..." -ForegroundColor Cyan
alembic upgrade head
python -m app.seed.catalog
python -m app.seed.followups
python -m app.seed.documents
Pop-Location

Write-Host "Demo environment reset complete." -ForegroundColor Green
