"""Revoke every persistent session belonging to one customer."""

from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.users.logout_all.dto import LogoutAllRequest
from app.users.shared.interfaces import SessionRepository, UserRepository


class LogoutAllService:
    def __init__(self, users: UserRepository, sessions: SessionRepository, uow: UnitOfWork) -> None:
        self.users = users
        self.sessions = sessions
        self.uow = uow

    def execute(self, payload: LogoutAllRequest) -> None:
        user = self.users.get_by_id(payload.user_id, for_update=True)
        if user is None:
            raise AppError(
                "invalid_session", "The session is invalid or expired. Sign in again.", 401
            )
        self.sessions.revoke_all(user.id)
        self.uow.commit()
