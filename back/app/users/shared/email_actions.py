"""Issue and validate one-use email action tokens without owning a transaction."""

from datetime import timedelta

from app.infrastructure.models import ActionToken, User, new_id
from app.shared.errors import AppError
from app.shared.ports import EmailSender
from app.shared.time import utcnow
from app.shared.tokens import generate_token, hash_token
from app.users.shared.interfaces import ActionTokenRepository, UserRepository


class EmailActionService:
    def __init__(
        self,
        users: UserRepository,
        actions: ActionTokenRepository,
        email: EmailSender,
        verification_minutes: int,
        reset_minutes: int,
    ) -> None:
        self.users, self.actions, self.email = users, actions, email
        self.verification_minutes, self.reset_minutes = verification_minutes, reset_minutes

    def queue_email_action(self, user: User, purpose: str) -> None:
        """The use-case service holds the user lock and commits the outbox."""
        minutes = self.verification_minutes if purpose == "verify_email" else self.reset_minutes
        raw_token = generate_token()
        self.actions.invalidate(user.id, purpose)
        self.actions.add(
            ActionToken(
                id=new_id(),
                user_id=user.id,
                token_type_id=self.actions.get_type_id(purpose),
                token_hash=hash_token(raw_token),
                expires_at=utcnow() + timedelta(minutes=minutes),
            )
        )
        self.email.send_action_email(user.email, purpose, raw_token)

    def require_action(self, raw_token: str, purpose: str) -> tuple[User, ActionToken]:
        digest = hash_token(raw_token)
        token = self.actions.find(digest, purpose)
        if token is None:
            raise AppError("invalid_action_token", "The link is invalid or expired.", 400)
        user = self.users.get_by_id(token.user_id, for_update=True)
        token = self.actions.find(digest, purpose, for_update=True)
        if (
            user is None
            or not user.is_active
            or token is None
            or token.consumed_at
            or token.expires_at <= utcnow()
        ):
            raise AppError("invalid_action_token", "The link is invalid or expired.", 400)
        return user, token
