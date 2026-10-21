"""Dependency injection for verify_email only."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.shared.dependencies import get_action_repository, get_email_actions, get_unit_of_work
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
)
from app.users.verify_email.interfaces import VerifyEmailServiceInterface
from app.users.verify_email.service import VerifyEmailService


def get_service(
    email_actions: Annotated[EmailActionServiceInterface, Depends(get_email_actions)],
    actions: Annotated[ActionTokenRepository, Depends(get_action_repository)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> VerifyEmailServiceInterface:
    return VerifyEmailService(email_actions, actions, uow)
