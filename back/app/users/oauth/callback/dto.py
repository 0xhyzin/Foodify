"""DTOs for OAuth callback."""

from typing import Annotated

from pydantic import StringConstraints

from app.shared.dto import APIModel


class OAuthCallbackRequest(APIModel):
    state: Annotated[
        str, StringConstraints(min_length=32, max_length=512, pattern=r"^[A-Za-z0-9_-]+$")
    ]
    code: Annotated[str, StringConstraints(min_length=1, max_length=4096)] | None = None
    error: Annotated[str, StringConstraints(max_length=255)] | None = None


class OAuthCallbackResult(APIModel):
    fragment: str
