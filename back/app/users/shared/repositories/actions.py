"""MySQL actions persistence adapter."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    ActionToken,
    Role,
    TokenType,
)
from app.shared.errors import AppError
from app.shared.time import utcnow


class SqlAlchemyActionTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_customer_role(self) -> Role:
        role = self.session.scalar(select(Role).where(Role.code == "customer"))
        if role is None:
            raise AppError(
                "configuration_error", "Account registration is temporarily unavailable.", 503
            )
        return role

    def get_type_id(self, purpose: str) -> int:
        token_type = self.session.scalar(select(TokenType).where(TokenType.code == purpose))
        if token_type is None:
            raise AppError(
                "configuration_error", "Account actions are temporarily unavailable.", 503
            )
        return token_type.id

    def find(self, token_hash: str, purpose: str, for_update: bool = False) -> ActionToken | None:
        statement = select(ActionToken).where(
            ActionToken.token_hash == token_hash,
            ActionToken.token_type_id == self.get_type_id(purpose),
        )
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(statement)

    def invalidate(self, user_id: str, purpose: str) -> None:
        self.session.execute(
            update(ActionToken)
            .where(
                ActionToken.user_id == user_id,
                ActionToken.token_type_id == self.get_type_id(purpose),
                ActionToken.consumed_at.is_(None),
            )
            .values(consumed_at=utcnow())
        )

    def add(self, token: ActionToken) -> None:
        self.session.add(token)
