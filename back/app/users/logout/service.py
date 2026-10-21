"""Revoke the session identified by an authenticated access token."""

from app.shared.errors import AppError
from app.shared.ports import TokenCodec, UnitOfWork
from app.shared.time import utcnow
from app.users.logout.dto import LogoutRequest
from app.users.shared.interfaces import SessionRepository, UserRepository


class LogoutService:
    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        tokens: TokenCodec,
        uow: UnitOfWork,
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.tokens = tokens
        self.uow = uow

    def execute(self, payload: LogoutRequest) -> None:
        claims = self.tokens.decode_access(payload.access_token)
        user = self.users.get_by_id(claims.user_id, for_update=True)
        session = self.sessions.get(claims.session_id, for_update=True)
        if user is None or session is None or session.user_id != user.id:
            raise AppError(
                "invalid_session", "The session is invalid or expired. Sign in again.", 401
            )
        session.revoked_at = utcnow()
        self.uow.commit()
