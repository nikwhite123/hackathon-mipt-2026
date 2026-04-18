"""Database startup: Alembic upgrade and idempotent bootstrap seeds (uvicorn and tests)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.settings import BASE_DIR, read_env_bool
from app.db.session import engine
from app.repositories.data_repository import get_data_repository
from app.services.bootstrap_service import BootstrapService

logger = logging.getLogger(__name__)


def run_alembic_upgrade() -> None:
    """Apply Alembic migrations to the current DATABASE_URL."""
    from alembic import command
    from alembic.config import Config

    from app.core.settings import settings

    ini_path = BASE_DIR / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


def run_bootstrap_seed() -> None:
    """Load reference data and organizations when tables are empty or already filled."""
    with Session(engine) as db:
        bootstrap = BootstrapService(get_data_repository())
        bootstrap.seed_reference_data(db)
        bootstrap.seed_organizations(db)


def run_database_startup() -> None:
    """Read RUN_* flags on each call (needed when tests change os.environ between imports)."""
    if read_env_bool("RUN_MIGRATIONS_ON_START", True):
        logger.info("Applying database migrations (alembic upgrade head)")
        run_alembic_upgrade()
    if read_env_bool("RUN_SEED_ON_START", True):
        logger.info("Running bootstrap seed (reference data + organizations)")
        run_bootstrap_seed()
