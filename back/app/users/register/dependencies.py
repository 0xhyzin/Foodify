"""Dependency injection for register only."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import PasswordHasher, UnitOfWork
from app.users.register.interfaces import RegisterServiceInterface
from app.users.register.service import RegisterService
from app.users.shared.dependencies import (
    get_action_repository,
    get_email_actions,
    get_password_hasher,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    UserRepository,
)


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    actions: Annotated[ActionTokenRepository, Depends(get_action_repository)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    email_actions: Annotated[EmailActionServiceInterface, Depends(get_email_actions)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> RegisterServiceInterface:
    return RegisterService(users, actions, hasher, email_actions, uow)
