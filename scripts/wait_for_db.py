"""Wait until DATABASE_URL accepts connections (Docker entrypoint / CI smoke)."""

from __future__ import annotations

import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError, OperationalError


def main() -> None:
    """Poll DB with `SELECT 1` until success or timeout; exit 1 on failure."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("wait_for_db: DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    max_seconds = int(os.environ.get("DB_WAIT_MAX_SECONDS", "120"))
    interval = float(os.environ.get("DB_WAIT_INTERVAL_SECONDS", "2"))
    deadline = time.monotonic() + max_seconds
    last_err: BaseException | None = None

    while time.monotonic() < deadline:
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("wait_for_db: database is reachable")
            return
        except (OperationalError, DatabaseError, OSError) as e:
            last_err = e
            print(f"wait_for_db: not ready ({e!r}), retry in {interval}s")
            time.sleep(interval)

    print(f"wait_for_db: timeout after {max_seconds}s, last error: {last_err!r}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
