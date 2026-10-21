"""DTOs owned by the register operation."""

from app.users.shared.dto.credentials import EmailRequest, Password
from app.users.shared.dto.messages import MessageResponse
from app.users.shared.dto.primitives import PersonName


class RegisterRequest(EmailRequest):
    name: PersonName
    password: Password


class RegisterResponse(MessageResponse):
    pass
