"""Run migrations against the explicitly selected APP_ENV configuration."""

from logging.config import fileConfig

from alembic import context

from app.core.config import get_settings
from app.infrastructure import models as _models  # noqa: F401
from app.infrastructure.database import Base, create_database_engine

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Render the selected database's SQL without opening a connection."""
    settings = get_settings()
    context.configure(
        url=settings.migration_database_url or settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations using the same connection settings as the application."""
    settings = get_settings()
    engine = create_database_engine(settings.migration_database_url or settings.database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
