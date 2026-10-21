"""DTOs for OAuth start."""

from typing import Annotated

from pydantic import StringConstraints

from app.shared.dto import APIModel


class StartOAuthRequest(APIModel):
    binding_challenge: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class StartOAuthResponse(APIModel):
    authorization_url: str
