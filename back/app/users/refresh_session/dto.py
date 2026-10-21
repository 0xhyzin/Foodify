"""Session refresh request and response contracts."""

from app.shared.dto import APIModel
from app.users.shared.dto.credentials import OpaqueToken
from app.users.shared.dto.tokens import TokenResponse


class RefreshRequest(APIModel):
    refresh_token: OpaqueToken


class RefreshResponse(TokenResponse):
    """The rotated access/refresh token pair and current customer profile."""
