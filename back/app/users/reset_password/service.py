"""Only the reset_password business use case."""

from app.shared.errors import AppError
from app.shared.ports import PasswordHasher, UnitOfWork
from app.shared.time import utcnow
from app.users.reset_password.dto import ResetPasswordRequest
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    SessionRepository,
)


class ResetPasswordService:
    def __init__(
        self,
        email_actions: EmailActionServiceInterface,
        hasher: PasswordHasher,
        actions: ActionTokenRepository,
        sessions: SessionRepository,
        uow: UnitOfWork,
    ) -> None:
        self.email_actions = email_actions
        self.hasher = hasher
        self.actions = actions
        self.sessions = sessions
        self.uow = uow

    def execute(self, payload: ResetPasswordRequest) -> None:
        raw_token, password = payload.token, payload.password
        # Hash before locking; reset and all session mutations lock the user.
        password_hash = self.hasher.hash(password)
        user, token = self.email_actions.require_action(raw_token, "password_reset")
        if user.password_hash is None or not user.is_email_verified:
            raise AppError("invalid_action_token", "The link is invalid or expired.", 400)
        user.password_hash = password_hash
        token.consumed_at = utcnow()
        self.actions.invalidate(user.id, "password_reset")
        self.sessions.revoke_all(user.id)
        self.uow.commit()
