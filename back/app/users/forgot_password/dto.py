"""DTOs owned by the forgot_password operation."""

from app.users.shared.dto.credentials import EmailRequest
from app.users.shared.dto.messages import MessageResponse


class ForgotPasswordRequest(EmailRequest):
    pass


class ForgotPasswordResponse(MessageResponse):
    pass
