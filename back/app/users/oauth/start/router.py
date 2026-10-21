"""HTTP presentation for OAuth start."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.users.oauth.start.dependencies import get_service
from app.users.oauth.start.dto import StartOAuthRequest, StartOAuthResponse
from app.users.oauth.start.interfaces import StartOAuthServiceInterface
from app.users.shared.enums import SocialProvider

router = APIRouter()


@router.post("/oauth/{provider}/start", response_model=StartOAuthResponse)
def start_social_sign_in(
    provider: SocialProvider,
    payload: StartOAuthRequest,
    service: Annotated[StartOAuthServiceInterface, Depends(get_service)],
) -> StartOAuthResponse:
    return service.execute(provider.value, payload)
