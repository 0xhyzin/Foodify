"""Only the verify_email business use case."""

from app.shared.ports import UnitOfWork
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
)
from app.users.verify_email.dto import VerifyEmailRequest
from app.users.verify_email.confirmation import confirm_email_token


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
        confirm_email_token(payload.token, self.email_actions, self.actions)
        self.uow.commit()
