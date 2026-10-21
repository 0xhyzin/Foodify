"""Password login request and response contracts."""

from typing import Annotated

from pydantic import StringConstraints

from app.users.shared.dto.credentials import EmailRequest
from app.users.shared.dto.tokens import TokenResponse


class LoginRequest(EmailRequest):
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class LoginResponse(TokenResponse):
    """The new session's tokens and public customer profile."""
