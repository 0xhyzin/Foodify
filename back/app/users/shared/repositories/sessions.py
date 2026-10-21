"""MySQL sessions persistence adapter."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    AuthSession,
    RefreshToken,
)
from app.shared.time import utcnow


class SqlAlchemySessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, session_id: str, for_update: bool = False) -> AuthSession | None:
        statement = select(AuthSession).where(AuthSession.id == session_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(statement)

    def add(self, session: AuthSession) -> None:
        self.session.add(session)

    def add_refresh(self, token: RefreshToken) -> None:
        self.session.add(token)

    def find_refresh(self, token_hash: str, for_update: bool = False) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(statement)

    def revoke_all(self, user_id: str) -> None:
        self.session.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
