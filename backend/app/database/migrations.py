import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)

# backend/app/database/migrations.py -> backend/alembic.ini
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ALEMBIC_INI = _BACKEND_ROOT / "alembic.ini"


def run_migrations() -> None:
    """Bring the database schema up to date by running every Alembic
    migration that hasn't been applied yet (`alembic upgrade head`).

    This replaces the old Base.metadata.create_all() + ad-hoc
    "add any missing columns" startup hook. Alembic tracks exactly which
    migrations have run in an `alembic_version` table, so this is safe to
    call on every startup:
      - fresh database  -> every migration runs, all tables get created.
      - up-to-date DB    -> no-op.
      - DB behind head   -> only the missing migrations run.

    Note: a database that was set up by the *old* startup hook (tables
    already exist, but there's no `alembic_version` table yet) needs a
    one-time `alembic stamp head` — see alembic/versions/0001_initial_schema.py.
    """
    logger.info("Running database migrations (alembic upgrade head)...")
    cfg = Config(str(_ALEMBIC_INI))
    command.upgrade(cfg, "head")
    logger.info("Database migrations complete.")