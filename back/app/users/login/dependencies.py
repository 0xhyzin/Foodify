"""Wire login's service to request-scoped repository and security adapters."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import PasswordHasher, UnitOfWork
from app.users.login.interfaces import LoginServiceInterface
from app.users.login.service import LoginService
from app.users.shared.dependencies import (
    get_dummy_hash,
    get_password_hasher,
    get_session_issuer,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import SessionIssuerInterface, UserRepository


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    session_issuer: Annotated[SessionIssuerInterface, Depends(get_session_issuer)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> LoginServiceInterface:
    return LoginService(users, hasher, session_issuer, uow, get_dummy_hash())
