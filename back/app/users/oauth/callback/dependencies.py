"""Local composition for OAuth callback."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import OAuthGateway, UnitOfWork
from app.users.oauth.callback.interfaces import OAuthCallbackServiceInterface
from app.users.oauth.callback.service import OAuthCallbackService
from app.users.shared.dependencies import (
    get_action_repository,
    get_email_actions,
    get_oauth_gateway,
    get_social_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    SocialRepository,
    UserRepository,
)


def get_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    social: Annotated[SocialRepository, Depends(get_social_repository)],
    actions: Annotated[ActionTokenRepository, Depends(get_action_repository)],
    gateway: Annotated[OAuthGateway, Depends(get_oauth_gateway)],
    email_actions: Annotated[EmailActionServiceInterface, Depends(get_email_actions)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> OAuthCallbackServiceInterface:
    return OAuthCallbackService(users, social, actions, gateway, email_actions, uow)
