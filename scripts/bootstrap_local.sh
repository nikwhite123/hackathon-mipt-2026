#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "python is required"
  exit 1
fi

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "Создайте файл .env (например: cp .env.example .env) и при необходимости поправьте DATABASE_URL."
  exit 1
fi

echo "[1/5] Starting Postgres"
docker compose up -d db

echo "[2/5] Waiting for Postgres healthcheck"
for _ in $(seq 1 30); do
  status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' rostelecom-postgres 2>/dev/null || true)"
  if [[ "$status" == "healthy" ]]; then
    break
  fi
  sleep 2
done

final_status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' rostelecom-postgres 2>/dev/null || true)"
if [[ "$final_status" != "healthy" ]]; then
  echo "Postgres container is not healthy"
  exit 1
fi

echo "[3/5] Applying migrations (DATABASE_URL из .env)"
python -m alembic upgrade head

echo "[4/5] Alembic current revision"
python -m alembic current

echo "[5/5] Importing seed and reference data"
python scripts/init_db.py

python scripts/verify_db.py

echo "Локальная БД готова. Подключение: см. DATABASE_URL в .env (часто localhost:5433)."
