"""Reject cross-origin cookie mutations before application use cases execute."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.origins import canonical_origin
from app.shared.errors import AppError


def require_browser_client(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    origin = request.headers.get("origin")
    try:
        normalized_origin = canonical_origin(origin or "")
    except ValueError:
        normalized_origin = None
    if (
        request.headers.get("x-foodify-client") != "web"
        or normalized_origin not in settings.browser_allowed_origins
    ):
        raise AppError("browser_request_rejected", "This browser request is not allowed.", 403)
