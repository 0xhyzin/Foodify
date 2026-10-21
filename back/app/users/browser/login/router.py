"""Present password login as an access response plus an HttpOnly cookie."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.config import Settings, get_settings
from app.dependencies import limit_email_action
from app.users.browser.shared.cookies import set_refresh_cookie
from app.users.browser.shared.dto import BrowserSessionResponse
from app.users.login.dependencies import get_service
from app.users.login.dto import LoginRequest
from app.users.login.interfaces import LoginServiceInterface

router = APIRouter()


@router.post("/login", response_model=BrowserSessionResponse)
def login_browser_customer(
    payload: LoginRequest,
    response: Response,
    service: Annotated[LoginServiceInterface, Depends(get_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BrowserSessionResponse:
    limit_email_action("login", payload.email, limit=10)
    tokens = service.execute(payload)
    set_refresh_cookie(response, tokens.refresh_token, settings)
    return BrowserSessionResponse.from_token_pair(tokens)
