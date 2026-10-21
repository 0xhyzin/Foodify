"""Rotate one refresh token and revoke sessions when token replay is detected."""

from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.shared.tokens import hash_token
from app.users.refresh_session.dto import RefreshRequest, RefreshResponse
from app.users.shared.interfaces import (
    SessionIssuerInterface,
    SessionRepository,
    UserRepository,
)


class RefreshSessionService:
    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        session_issuer: SessionIssuerInterface,
        uow: UnitOfWork,
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.session_issuer = session_issuer
        self.uow = uow

    def execute(self, payload: RefreshRequest) -> RefreshResponse:
        digest = hash_token(payload.refresh_token)
        refresh = self.sessions.find_refresh(digest)
        session = self.sessions.get(refresh.session_id) if refresh else None
        if session is None:
            raise self._invalid_session()
        user = self.users.get_by_id(session.user_id, for_update=True)
        session = self.sessions.get(session.id, for_update=True)
        refresh = self.sessions.find_refresh(digest, for_update=True)
        if (
            user is None
            or not user.is_active
            or not user.is_email_verified
            or session is None
            or refresh is None
        ):
            raise self._invalid_session()
        if refresh.used_at is not None:
            # Revocation must survive the error response and request rollback.
            session.revoked_at = utcnow()
            self.uow.commit()
            raise self._invalid_session()
        if session.revoked_at is not None or session.expires_at <= utcnow():
            raise self._invalid_session()
        refresh.used_at = utcnow()
        response = self.session_issuer.issue_token_pair(user, session)
        self.uow.commit()
        return RefreshResponse.model_validate(response)

    @staticmethod
    def _invalid_session() -> AppError:
        return AppError("invalid_session", "The session is invalid or expired. Sign in again.", 401)
