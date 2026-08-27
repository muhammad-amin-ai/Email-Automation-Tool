from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- app wiring -------------------------------------------------------
# `prepend_sys_path = .` in alembic.ini (run from the backend/ directory)
# puts backend/ on sys.path, so the app package imports the same way it
# does for uvicorn.
#
# Importing app.database.connection builds DATABASE_URL from the same
# app.core.config.settings (i.e. the same .env) the app itself uses, and
# — as a side effect — makes sure the target database exists (via
# CREATE DATABASE IF NOT EXISTS) before alembic tries to connect to it.
# This keeps DB credentials defined in exactly one place instead of
# duplicating them into alembic.ini.
from app.database.connection import DATABASE_URL  # noqa: E402
from app.database.base import Base  # noqa: E402
import app.models  # noqa: E402,F401  (registers all models on Base.metadata)

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata
# ------------------------------------------------------------------------

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
