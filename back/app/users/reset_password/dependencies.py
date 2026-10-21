"""Dependency injection for reset_password only."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import PasswordHasher, UnitOfWork
from app.users.reset_password.interfaces import ResetPasswordServiceInterface
from app.users.reset_password.service import ResetPasswordService
from app.users.shared.dependencies import (
    get_action_repository,
    get_email_actions,
    get_password_hasher,
    get_session_repository,
    get_unit_of_work,
)
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    SessionRepository,
)


def get_service(
    email_actions: Annotated[EmailActionServiceInterface, Depends(get_email_actions)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    actions: Annotated[ActionTokenRepository, Depends(get_action_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> ResetPasswordServiceInterface:
    return ResetPasswordService(email_actions, hasher, actions, sessions, uow)
