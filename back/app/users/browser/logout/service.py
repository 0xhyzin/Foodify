"""Idempotently revoke the session identified by a current or rotated refresh token."""

from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.shared.tokens import hash_token
from app.users.browser.logout.dto import BrowserLogoutRequest
from app.users.shared.interfaces import SessionRepository, UserRepository


class BrowserLogoutService:
    def __init__(self, users: UserRepository, sessions: SessionRepository, uow: UnitOfWork) -> None:
        self.users = users
        self.sessions = sessions
        self.uow = uow

    def execute(self, payload: BrowserLogoutRequest) -> None:
        if not payload.refresh_token:
            return
        refresh = self.sessions.find_refresh(hash_token(payload.refresh_token))
        session = self.sessions.get(refresh.session_id) if refresh else None
        if session is None:
            return
        # Keep the same user -> session lock order as refresh/password operations.
        self.users.get_by_id(session.user_id, for_update=True)
        session = self.sessions.get(session.id, for_update=True)
        if session is None:
            return
        if session.revoked_at is None:
            session.revoked_at = utcnow()
        self.uow.commit()
