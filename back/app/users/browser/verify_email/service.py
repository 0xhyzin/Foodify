"""Consume email proof and issue its owner's session in one transaction."""

from app.shared.ports import UnitOfWork
from app.users.shared.dto.tokens import TokenResponse
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    SessionIssuerInterface,
)
from app.users.verify_email.confirmation import confirm_email_token
from app.users.verify_email.dto import VerifyEmailRequest


class VerifyBrowserEmailService:
    def __init__(
        self,
        email_actions: EmailActionServiceInterface,
        actions: ActionTokenRepository,
        issuer: SessionIssuerInterface,
        uow: UnitOfWork,
    ) -> None:
        self.email_actions, self.actions = email_actions, actions
        self.issuer, self.uow = issuer, uow

    def execute(self, payload: VerifyEmailRequest) -> TokenResponse:
        try:
            # require_action holds the active owner/token locks and rejects expired or used proof.
            user = confirm_email_token(payload.token, self.email_actions, self.actions)
            tokens = self.issuer.create_session(user)
            self.uow.commit()
        except Exception:
            # Never consume the proof unless both verification and session persistence succeed.
            self.uow.rollback()
            raise
        return tokens
