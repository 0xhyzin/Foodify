"""Local composition for OAuth complete."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.oauth.complete.interfaces import CompleteOAuthServiceInterface
from app.users.oauth.complete.service import CompleteOAuthService
from app.users.shared.dependencies import (
    get_session_issuer,
    get_social_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import (
    SessionIssuerInterface,
    SocialRepository,
    UserRepository,
)


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    social: Annotated[SocialRepository, Depends(get_social_repository)],
    issuer: Annotated[SessionIssuerInterface, Depends(get_session_issuer)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> CompleteOAuthServiceInterface:
    return CompleteOAuthService(users, social, issuer, uow)
