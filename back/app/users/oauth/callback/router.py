"""HTTP presentation for OAuth callback."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.shared.errors import AppError
from app.users.oauth.callback.dependencies import get_service
from app.users.oauth.callback.dto import OAuthCallbackRequest
from app.users.oauth.callback.interfaces import OAuthCallbackServiceInterface
from app.users.shared.enums import SocialProvider

router = APIRouter()


@router.get("/oauth/{provider}/callback", response_class=RedirectResponse)
def finish_provider_callback(
    provider: SocialProvider,
    service: Annotated[OAuthCallbackServiceInterface, Depends(get_service)],
    state: Annotated[str, Query(min_length=32, max_length=512, pattern=r"^[A-Za-z0-9_-]+$")],
    code: Annotated[str | None, Query(min_length=1, max_length=4096)] = None,
    error: Annotated[str | None, Query(max_length=255)] = None,
) -> RedirectResponse:
    try:
        result = service.execute(
            provider.value, OAuthCallbackRequest(state=state, code=code, error=error)
        )
        fragment = result.fragment
    except AppError as exc:
        # Never reflect provider error text, codes, tokens or arbitrary redirect URLs.
        allowed_errors = {
            "invalid_oauth_state",
            "oauth_cancelled",
            "oauth_failed",
            "oauth_email_required",
            "oauth_account_link_required",
            "email_verification_required",
            "oauth_unavailable",
        }
        error_code = exc.code if exc.code in allowed_errors else "oauth_failed"
        fragment = f"error={error_code}"
    return RedirectResponse(
        f"{get_settings().frontend_url.rstrip('/')}/oauth/callback#{fragment}",
        status_code=303,
    )
