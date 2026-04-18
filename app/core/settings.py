"""Load `.env` and application settings (database, JWT, metrics). Migrations and seeds use `RUN_*` in `app.db.startup`."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"


def load_env_file(env_path: Path = ENV_PATH) -> None:
    """Parse KEY=VALUE lines from a file and set os.environ via setdefault (does not override existing keys)."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def read_env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean flag from the environment (safe to call after mutating os.environ)."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


load_env_file()


@dataclass(frozen=True)
class Settings:
    """Environment-backed configuration after load_env_file()."""

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    access_token_expire_minutes: int = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "text")
    enable_metrics: bool = read_env_bool("ENABLE_METRICS", True)


settings = Settings()
