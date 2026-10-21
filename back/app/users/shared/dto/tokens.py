"""Common JSON token-pair shape, without endpoint orchestration."""

from typing import Literal

from app.shared.dto import APIModel
from app.users.shared.dto.profile import UserResponse


class TokenResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse
