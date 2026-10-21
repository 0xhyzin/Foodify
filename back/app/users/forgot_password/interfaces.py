"""Business boundary for forgot_password."""

from typing import Protocol

from app.users.forgot_password.dto import ForgotPasswordRequest


class ForgotPasswordServiceInterface(Protocol):
    def execute(self, payload: ForgotPasswordRequest) -> None: ...
