#!/usr/bin/env python3
"""Verify Postgres: Alembic revision present and core tables row counts (dev/CI health script)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text

from app.core.settings import settings


def main() -> int:
    """Check alembic_version and row counts; exit 0 on success, 1 on connection or schema errors."""
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            if not rev:
                print("Error: alembic_version is empty. Run: python -m alembic upgrade head")
                return 1
            print(f"Alembic revision in DB: {rev}")

            checks = (
                "organizations",
                "users",
                "incidents",
                "fstec_threats",
                "organization_settings",
            )
            for table in checks:
                n = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table}: {int(n)} rows")

            orgs = int(conn.execute(text("SELECT COUNT(*) FROM organizations")).scalar() or 0)
            incidents = int(conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar() or 0)
            if orgs == 0:
                print("Warning: organizations is empty. Run: python scripts/init_db.py")
            if incidents == 0:
                print("Warning: incidents is empty. Check data/*.xlsx then run: python scripts/init_db.py")
    except OSError as e:
        print(f"Database connection error ({settings.database_url!r}): {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    print("Check passed: database reachable and core tables exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
