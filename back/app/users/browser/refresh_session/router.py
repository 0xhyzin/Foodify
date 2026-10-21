"""Rotate the refresh cookie without exposing it in the request or response JSON."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.shared.errors import AppError, error_response
from app.users.browser.shared.cookies import (
    REFRESH_COOKIE_NAME,
    clear_refresh_cookie,
    set_refresh_cookie,
)
from app.users.browser.shared.dto import BrowserSessionResponse
from app.users.refresh_session.dependencies import get_service
from app.users.refresh_session.dto import RefreshRequest
from app.users.refresh_session.interfaces import RefreshSessionServiceInterface

router = APIRouter()


@router.post("/refresh", response_model=BrowserSessionResponse)
def refresh_browser_session(
    request: Request,
    response: Response,
    service: Annotated[RefreshSessionServiceInterface, Depends(get_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BrowserSessionResponse | Response:
    try:
        raw_token = request.cookies.get(REFRESH_COOKIE_NAME, "")
        try:
            payload = RefreshRequest(refresh_token=raw_token)
        except ValidationError:
            raise AppError(
                "invalid_session", "The session is invalid or expired. Sign in again.", 401
            ) from None
        tokens = service.execute(payload)
    except AppError as exc:
        rejected = error_response(
            request,
            exc.code,
            exc.message,
            exc.status_code,
            exc.details,
            {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None,
        )
        if exc.status_code == 401:
            clear_refresh_cookie(rejected, settings)
        return rejected
    set_refresh_cookie(response, tokens.refresh_token, settings)
    return BrowserSessionResponse.from_token_pair(tokens)
