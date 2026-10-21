"""Only the forgot_password business use case."""

from app.shared.ports import UnitOfWork
from app.users.forgot_password.dto import ForgotPasswordRequest
from app.users.shared.interfaces import (
    EmailActionServiceInterface,
    UserRepository,
)


class ForgotPasswordService:
    def __init__(
        self, users: UserRepository, email_actions: EmailActionServiceInterface, uow: UnitOfWork
    ) -> None:
        self.users = users
        self.email_actions = email_actions
        self.uow = uow

    def execute(self, payload: ForgotPasswordRequest) -> None:
        email = payload.email
        user = self.users.get_by_email(email)
        if user is None:
            return
        user = self.users.get_by_id(user.id, for_update=True)
        # Social-only accounts recover through their provider, not local reset.
        if user is not None and user.is_active and user.password_hash and user.is_email_verified:
            self.email_actions.queue_email_action(user, "password_reset")
            self.uow.commit()
