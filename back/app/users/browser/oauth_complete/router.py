"""Exchange the browser-bound OAuth ticket and issue an HttpOnly refresh cookie."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.config import Settings, get_settings
from app.users.browser.shared.cookies import set_refresh_cookie
from app.users.browser.shared.dto import BrowserSessionResponse
from app.users.oauth.complete.dependencies import get_service
from app.users.oauth.complete.dto import CompleteOAuthRequest
from app.users.oauth.complete.interfaces import CompleteOAuthServiceInterface

router = APIRouter()


@router.post("/oauth/complete", response_model=BrowserSessionResponse)
def complete_browser_social_sign_in(
    payload: CompleteOAuthRequest,
    response: Response,
    service: Annotated[CompleteOAuthServiceInterface, Depends(get_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BrowserSessionResponse:
    tokens = service.execute(payload)
    set_refresh_cookie(response, tokens.refresh_token, settings)
    return BrowserSessionResponse.from_token_pair(tokens)
