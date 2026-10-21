"""Host-only refresh cookies stay outside browser JavaScript and JSON DTOs."""

from fastapi import Response

from app.core.config import Settings

REFRESH_COOKIE_NAME = "foodify_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth/browser"


def set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        secure=settings.browser_cookie_secure,
        httponly=True,
        samesite=settings.browser_cookie_same_site,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=settings.browser_cookie_secure,
        httponly=True,
        samesite=settings.browser_cookie_same_site,
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
