"""Expose email confirmation through the protected browser cookie transport."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.config import Settings, get_settings
from app.users.browser.shared.cookies import set_refresh_cookie
from app.users.browser.shared.dto import BrowserSessionResponse
from app.users.browser.verify_email.dependencies import get_service
from app.users.browser.verify_email.interfaces import VerifyBrowserEmailServiceInterface
from app.users.verify_email.dto import VerifyEmailRequest

router = APIRouter()


@router.post("/verify-email", response_model=BrowserSessionResponse)
def confirm_browser_customer_email(
    payload: VerifyEmailRequest,
    response: Response,
    service: Annotated[VerifyBrowserEmailServiceInterface, Depends(get_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BrowserSessionResponse:
    tokens = service.execute(payload)
    set_refresh_cookie(response, tokens.refresh_token, settings)
    return BrowserSessionResponse.from_token_pair(tokens)
