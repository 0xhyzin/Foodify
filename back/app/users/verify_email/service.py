"""Only the verify_email business use case."""

from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
)
from app.users.verify_email.dto import VerifyEmailRequest


class VerifyEmailService:
    def __init__(
        self,
        email_actions: EmailActionServiceInterface,
        actions: ActionTokenRepository,
        uow: UnitOfWork,
    ) -> None:
        self.email_actions = email_actions
        self.actions = actions
        self.uow = uow

    def execute(self, payload: VerifyEmailRequest) -> None:
        raw_token = payload.token
        user, token = self.email_actions.require_action(raw_token, "verify_email")
        user.is_email_verified = True
        token.consumed_at = utcnow()
        self.actions.invalidate(user.id, "verify_email")
        self.uow.commit()
