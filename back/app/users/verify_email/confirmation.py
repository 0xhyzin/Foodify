"""Confirm the locked token owner's email inside the caller's transaction."""

from app.infrastructure.models import User
from app.shared.time import utcnow
from app.users.shared.interfaces import ActionTokenRepository, EmailActionServiceInterface


def confirm_email_token(
    raw_token: str,
    email_actions: EmailActionServiceInterface,
    actions: ActionTokenRepository,
) -> User:
    user, token = email_actions.require_action(raw_token, "verify_email")
    user.is_email_verified = True
    token.consumed_at = utcnow()
    actions.invalidate(user.id, "verify_email")
    return user
