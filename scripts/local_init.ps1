param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".env")) {
    Copy-Item ".env.local.example" ".env"
    Write-Host "Created .env from .env.local.example"
}

Write-Host "Starting local PostgreSQL + Redis..."
docker compose -f docker-compose.local.yml up -d

if (-not $SkipInstall) {
    Write-Host "Installing Python dependencies..."
    python -m pip install -r requirements.txt
}

Write-Host "Running migrations..."
alembic upgrade head

Write-Host "Seeding local data..."
python scripts/seed_local_data.py

Write-Host "Done. Start server with:"
Write-Host "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
