"""Wire current-session logout to storage, token decoding and a transaction."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import TokenCodec, UnitOfWork
from app.users.logout.interfaces import LogoutServiceInterface
from app.users.logout.service import LogoutService
from app.users.shared.dependencies import (
    get_session_repository,
    get_token_codec,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import SessionRepository, UserRepository


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    tokens: Annotated[TokenCodec, Depends(get_token_codec)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> LogoutServiceInterface:
    return LogoutService(users, sessions, tokens, uow)
