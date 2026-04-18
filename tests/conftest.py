"""Pytest bootstrap: isolated SQLite DB, env flags, migrations + seed before importing the app."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DB_PATH = ROOT / "test_app.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["RUN_MIGRATIONS_ON_START"] = "true"
os.environ["RUN_SEED_ON_START"] = "true"
os.environ.setdefault("LOG_FORMAT", "text")

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

from app.db.startup import run_database_startup

run_database_startup()

os.environ["RUN_MIGRATIONS_ON_START"] = "false"
os.environ["RUN_SEED_ON_START"] = "false"
