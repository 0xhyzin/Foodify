"""Wire refresh-backed logout to existing repositories and transaction ownership."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.browser.logout.interfaces import BrowserLogoutServiceInterface
from app.users.browser.logout.service import BrowserLogoutService
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
) -> BrowserLogoutServiceInterface:
    return BrowserLogoutService(users, sessions, uow)
