"""Logout requires the protected browser request boundary, never a live access JWT."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.config import Settings, get_settings
from app.users.browser.logout.dependencies import get_service
from app.users.browser.logout.dto import BrowserLogoutRequest
from app.users.browser.logout.interfaces import BrowserLogoutServiceInterface
from app.users.browser.shared.cookies import REFRESH_COOKIE_NAME, clear_refresh_cookie

router = APIRouter()


@router.post("/logout", status_code=204)
def logout_browser_session(
    request: Request,
    service: Annotated[BrowserLogoutServiceInterface, Depends(get_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    service.execute(BrowserLogoutRequest(refresh_token=request.cookies.get(REFRESH_COOKIE_NAME)))
    response = Response(status_code=204)
    clear_refresh_cookie(response, settings)
    return response
