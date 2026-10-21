"""HTTP presentation for OAuth complete."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.users.oauth.complete.dependencies import get_service
from app.users.oauth.complete.dto import CompleteOAuthRequest, CompleteOAuthResponse
from app.users.oauth.complete.interfaces import CompleteOAuthServiceInterface

router = APIRouter()


@router.post("/oauth/complete", response_model=CompleteOAuthResponse)
def complete_social_sign_in(
    payload: CompleteOAuthRequest,
    service: Annotated[CompleteOAuthServiceInterface, Depends(get_service)],
) -> CompleteOAuthResponse:
    return service.execute(payload)
