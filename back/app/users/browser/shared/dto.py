"""Browser responses intentionally exclude the refresh token."""

from typing import Literal

from app.shared.dto import APIModel
from app.users.shared.dto.profile import UserResponse
from app.users.shared.dto.tokens import TokenResponse


class BrowserSessionResponse(APIModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse

    @classmethod
    def from_token_pair(cls, tokens: TokenResponse) -> "BrowserSessionResponse":
        return cls(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
            user=tokens.user,
        )
