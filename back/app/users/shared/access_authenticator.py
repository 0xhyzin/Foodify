"""Resolve the active customer for a verified access token and live session."""

from app.infrastructure.models import User
from app.shared.errors import AppError
from app.shared.ports import TokenCodec
from app.shared.time import utcnow
from app.users.shared.interfaces import SessionRepository, UserRepository


class AccessAuthenticator:
    def __init__(
        self, users: UserRepository, sessions: SessionRepository, tokens: TokenCodec
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.tokens = tokens

    def authenticate_access(self, raw_token: str) -> User:
        claims = self.tokens.decode_access(raw_token)
        session = self.sessions.get(claims.session_id)
        if (
            session is None
            or session.user_id != claims.user_id
            or session.revoked_at is not None
            or session.expires_at <= utcnow()
        ):
            raise self._invalid_session()
        user = self.users.get_by_id(claims.user_id)
        if user is None or not user.is_active or not user.is_email_verified:
            raise self._invalid_session()
        return user

    @staticmethod
    def _invalid_session() -> AppError:
        return AppError("invalid_session", "The session is invalid or expired. Sign in again.", 401)
