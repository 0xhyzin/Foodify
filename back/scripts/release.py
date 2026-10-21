"""Apply migrations with the schema login, then seed using the restricted API login."""

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from time import sleep

from app.core.config import PROJECT_ROOT, get_settings
from app.infrastructure.database import create_database_engine
from scripts.seed import main as seed_reference_data


def main() -> None:
    settings = get_settings()
    engine = create_database_engine(settings.migration_database_url or settings.database_url)
    try:
        for attempt in range(30):
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                break
            except SQLAlchemyError:
                if attempt == 29:
                    raise SystemExit("Database is not ready for release preparation.") from None
                sleep(2)
    finally:
        engine.dispose()
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    seed_reference_data()
    print("Release preparation completed. Existing user data was preserved.")


if __name__ == "__main__":
    main()
