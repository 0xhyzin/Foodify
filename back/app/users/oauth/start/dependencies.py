"""Local composition for OAuth start."""

from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.shared.ports import OAuthGateway, UnitOfWork
from app.users.oauth.start.interfaces import StartOAuthServiceInterface
from app.users.oauth.start.service import StartOAuthService
from app.users.shared.dependencies import get_oauth_gateway, get_social_repository, get_unit_of_work
from app.users.shared.interfaces import (
    SocialRepository,
)


def get_service(
    social: Annotated[SocialRepository, Depends(get_social_repository)],
    gateway: Annotated[OAuthGateway, Depends(get_oauth_gateway)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> StartOAuthServiceInterface:
    return StartOAuthService(social, gateway, uow, get_settings().oauth_state_minutes)
