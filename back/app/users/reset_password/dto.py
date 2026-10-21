"""DTOs owned by the reset_password operation."""

from app.shared.dto import APIModel
from app.users.shared.dto.credentials import OpaqueToken, Password
from app.users.shared.dto.messages import MessageResponse


class ResetPasswordRequest(APIModel):
    token: OpaqueToken
    password: Password


class ResetPasswordResponse(MessageResponse):
    pass
