"""MySQL user persistence adapter."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.models import Role, User


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: str, for_update: bool = False) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        if for_update:
            # Refresh the identity-map entry after obtaining the lock: the
            # authentication dependency can have loaded it before a concurrent
            # request changed its default address.
            statement = statement.with_for_update().execution_options(
                populate_existing=True,
            )
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )

    def add(self, user: User) -> None:
        self.session.add(user)
