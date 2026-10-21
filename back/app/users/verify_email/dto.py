"""DTOs owned by the verify_email operation."""

from app.shared.dto import APIModel
from app.users.shared.dto.credentials import OpaqueToken
from app.users.shared.dto.messages import MessageResponse


class VerifyEmailRequest(APIModel):
    token: OpaqueToken


class VerifyEmailResponse(MessageResponse):
    pass
