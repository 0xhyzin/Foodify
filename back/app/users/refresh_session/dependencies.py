"""Wire refresh rotation to repositories, session issuance and a transaction."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.refresh_session.interfaces import RefreshSessionServiceInterface
from app.users.refresh_session.service import RefreshSessionService
from app.users.shared.dependencies import (
    get_session_issuer,
    get_session_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import (
    SessionIssuerInterface,
    SessionRepository,
    UserRepository,
)


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    session_issuer: Annotated[SessionIssuerInterface, Depends(get_session_issuer)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> RefreshSessionServiceInterface:
    return RefreshSessionService(users, sessions, session_issuer, uow)
