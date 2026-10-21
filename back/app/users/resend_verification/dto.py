"""DTOs owned by the resend_verification operation."""

from app.users.shared.dto.credentials import EmailRequest
from app.users.shared.dto.messages import MessageResponse


class ResendVerificationRequest(EmailRequest):
    pass


class ResendVerificationResponse(MessageResponse):
    pass
