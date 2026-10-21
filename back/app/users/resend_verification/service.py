"""Only the resend_verification business use case."""

from app.shared.ports import UnitOfWork
from app.users.resend_verification.dto import ResendVerificationRequest
from app.users.shared.interfaces import (
    EmailActionServiceInterface,
    UserRepository,
)


class ResendVerificationService:
    def __init__(
        self, users: UserRepository, email_actions: EmailActionServiceInterface, uow: UnitOfWork
    ) -> None:
        self.users = users
        self.email_actions = email_actions
        self.uow = uow

    def execute(self, payload: ResendVerificationRequest) -> None:
        email = payload.email
        user = self.users.get_by_email(email)
        if user is None:
            return
        user = self.users.get_by_id(user.id, for_update=True)
        if user is not None and user.is_active and not user.is_email_verified:
            self.email_actions.queue_email_action(user, "verify_email")
            self.uow.commit()
