"""DTOs for OAuth complete."""

from typing import Annotated

from pydantic import StringConstraints

from app.shared.dto import APIModel
from app.users.shared.dto.credentials import OpaqueToken
from app.users.shared.dto.tokens import TokenResponse


class CompleteOAuthRequest(APIModel):
    ticket: OpaqueToken
    binding_verifier: Annotated[
        str, StringConstraints(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    ]


class CompleteOAuthResponse(TokenResponse):
    pass
