# Start the Industrial Engineering Copilot local demo environment.
# Requires: Docker, Python 3.12+, Node.js 22+, .env with GROQ_API_KEY

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting infrastructure (PostgreSQL, Redis, MinIO)..." -ForegroundColor Cyan
Push-Location $Root
docker compose up -d postgres redis minio
Pop-Location

Write-Host ""
Write-Host "Backend setup (migrations + demo seeds)..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "backend")

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]" | Out-Null

Write-Host "Running Alembic migrations..."
alembic upgrade head

Write-Host "Seeding demo data (idempotent)..."
python -m app.seed.catalog
python -m app.seed.followups
python -m app.seed.documents

Write-Host ""
Write-Host "Local startup complete." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  Terminal 1: cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8020"
Write-Host "  Terminal 2: cd frontend; npm install; npm run dev"
Write-Host ""
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  API docs: http://localhost:8020/docs"
Pop-Location
