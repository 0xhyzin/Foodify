"""Translate storage-specific transaction failures at the adapter boundary."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.shared.errors import PersistenceConflict


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session) -> None:
        self.session = session

    def flush(self) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise PersistenceConflict() from exc

    def commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            raise PersistenceConflict() from exc

    def rollback(self) -> None:
        self.session.rollback()
