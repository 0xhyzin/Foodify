"""Business boundary for reset_password."""

from typing import Protocol

from app.users.reset_password.dto import ResetPasswordRequest


class ResetPasswordServiceInterface(Protocol):
    def execute(self, payload: ResetPasswordRequest) -> None: ...
