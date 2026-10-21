"""MySQL SQLAlchemy connection lifecycle; schema changes belong to Alembic."""

from collections.abc import Generator
from functools import lru_cache

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import PROJECT_ROOT, get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return create_database_engine(settings.database_url)


def create_database_engine(database_url: str) -> Engine:
    settings = get_settings()
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        connect_args={
            "charset": "utf8mb4", "connect_timeout": 10,
            "init_command": "SET SESSION time_zone='+00:00'",
        },
        hide_parameters=True,
        echo=False,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@lru_cache(maxsize=1)
def get_expected_revision_heads() -> frozenset[str]:
    """Read this release's migration heads without opening a database connection."""
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    return frozenset(ScriptDirectory.from_config(config).get_heads())


def check_database_readiness() -> None:
    """Require a reachable database at this release's complete schema revision."""
    with get_engine().connect() as connection:
        applied = frozenset(MigrationContext.configure(connection).get_current_heads())
        if not applied or applied != get_expected_revision_heads():
            raise RuntimeError("Database schema does not match this release.")
