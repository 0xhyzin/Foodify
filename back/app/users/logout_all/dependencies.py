"""Wire all-sessions logout to customer/session storage and a transaction."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.logout_all.interfaces import LogoutAllServiceInterface
from app.users.logout_all.service import LogoutAllService
from app.users.shared.dependencies import (
    get_session_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import SessionRepository, UserRepository


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> LogoutAllServiceInterface:
    return LogoutAllService(users, sessions, uow)
