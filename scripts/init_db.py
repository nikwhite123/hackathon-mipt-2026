"""CLI: run bootstrap seed only (migrations: `alembic upgrade head` or app start with RUN_MIGRATIONS_ON_START)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.settings import settings
from app.db.startup import run_bootstrap_seed


def main() -> None:
    """Populate reference tables from files when empty; prints DATABASE_URL on success."""
    run_bootstrap_seed()
    print(f"Bootstrap seed completed for {settings.database_url}")


if __name__ == "__main__":
    main()
