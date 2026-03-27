param(
    [switch]$SkipInstall,
    [switch]$SkipSeed,
    [switch]$NoDocker,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $repoRoot

$pythonExe = ".\.venv\Scripts\python.exe"
$alembicExe = ".\.venv\Scripts\alembic.exe"

function Invoke-Step {
    param(
        [string]$File,
        [string[]]$CommandArgs
    )

    & $File @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $File $($CommandArgs -join ' ')"
    }
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    Invoke-Step "python" @("-m", "venv", ".venv")
}

Write-Host "Upgrading pip..."
Invoke-Step $pythonExe @("-m", "pip", "install", "--upgrade", "pip")

if (-not $SkipInstall) {
    Write-Host "Installing dependencies..."
    Invoke-Step $pythonExe @("-m", "pip", "install", "-r", "requirements.txt")

    Write-Host "Applying bcrypt compatibility versions..."
    Invoke-Step $pythonExe @("-m", "pip", "install", "--force-reinstall", "passlib==1.7.4", "bcrypt==4.0.1")
}

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.local.example") {
        Copy-Item ".env.local.example" ".env"
    }
    elseif (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
    }
    else {
        throw ".env template not found."
    }
    Write-Host "Created .env"
}

if (-not $NoDocker) {
    Write-Host "Starting PostgreSQL and Redis..."
    try {
        Invoke-Step "docker" @("compose", "-f", "docker-compose.local.yml", "up", "-d", "postgres", "redis")
    }
    catch {
        Write-Warning "Docker 启动依赖失败，将继续后续步骤。请确保 PostgreSQL(5432) 与 Redis(6380) 已可用。"
    }
}

if (-not (Test-Path $alembicExe)) {
    throw "alembic not found. Remove -SkipInstall or install dependencies first."
}

Write-Host "Running migrations..."
Invoke-Step $alembicExe @("upgrade", "head")

if (-not $SkipSeed) {
    if (Test-Path "scripts\seed_demo_data.py") {
        Write-Host "Seeding demo data..."
        Invoke-Step $pythonExe @("scripts\seed_demo_data.py")
    }
    elseif (Test-Path "scripts\seed_local_data.py") {
        Write-Host "Seeding local data..."
        Invoke-Step $pythonExe @("scripts\seed_local_data.py")
    }
}

Write-Host "Starting backend: http://127.0.0.1:$Port"
Invoke-Step $pythonExe @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port", "--reload")
