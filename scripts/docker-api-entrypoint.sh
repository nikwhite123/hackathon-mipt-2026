#!/usr/bin/env bash
set -euo pipefail

cd /app

is_true() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

if is_true "${WAIT_FOR_DB:-true}"; then
  python scripts/wait_for_db.py
fi

# Миграции и сиды выполняются в lifespan FastAPI (`RUN_MIGRATIONS_ON_START`, `RUN_SEED_ON_START`).

exec "$@"
