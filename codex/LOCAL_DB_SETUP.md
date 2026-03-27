# Local Database Storage Guide

This project now supports local persistent storage with Docker volumes.

## 1. What is stored locally

- PostgreSQL data directory: `data/postgres`
- Redis AOF data directory: `data/redis`

These folders are on your machine, so data remains after restarts.

## 2. Local environment config

Use `.env` (already created) or copy from `.env.local.example`.

Important values:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/study_room`
- `REDIS_URL=redis://127.0.0.1:6379/0`

## 3. One-command local initialization

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_init.ps1
```

What this script does:

1. Creates `.env` if missing.
2. Starts local PostgreSQL + Redis via `docker-compose.local.yml`.
3. Installs dependencies (unless `-SkipInstall`).
4. Runs `alembic upgrade head`.
5. Inserts local seed data (`scripts/seed_local_data.py`).

## 4. Manual commands (if preferred)

```powershell
docker compose -f docker-compose.local.yml up -d
python -m pip install -r requirements.txt
alembic upgrade head
python scripts/seed_local_data.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 5. Verify local storage

```powershell
docker compose -f docker-compose.local.yml ps
```

Check API:

- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/student`
- `http://127.0.0.1:8000/ui`

## 6. Reset local data (optional)

```powershell
docker compose -f docker-compose.local.yml down
Remove-Item -Recurse -Force data/postgres
Remove-Item -Recurse -Force data/redis
```
