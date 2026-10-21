"""Dependency injection for forgot_password only."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.forgot_password.interfaces import ForgotPasswordServiceInterface
from app.users.forgot_password.service import ForgotPasswordService
from app.users.shared.dependencies import get_email_actions, get_unit_of_work, get_user_repository
from app.users.shared.interfaces import (
    EmailActionServiceInterface,
    UserRepository,
)


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    email_actions: Annotated[EmailActionServiceInterface, Depends(get_email_actions)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> ForgotPasswordServiceInterface:
    return ForgotPasswordService(users, email_actions, uow)
