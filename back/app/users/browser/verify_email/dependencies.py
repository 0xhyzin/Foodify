"""Inject one shared transaction into confirmation and session persistence."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.browser.verify_email.interfaces import VerifyBrowserEmailServiceInterface
from app.users.browser.verify_email.service import VerifyBrowserEmailService
from app.users.shared.dependencies import (
    get_action_repository,
    get_email_actions,
    get_session_issuer,
    get_unit_of_work,
)
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    SessionIssuerInterface,
)


def get_service(
    email_actions: Annotated[EmailActionServiceInterface, Depends(get_email_actions)],
    actions: Annotated[ActionTokenRepository, Depends(get_action_repository)],
    issuer: Annotated[SessionIssuerInterface, Depends(get_session_issuer)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> VerifyBrowserEmailServiceInterface:
    return VerifyBrowserEmailService(email_actions, actions, issuer, uow)
