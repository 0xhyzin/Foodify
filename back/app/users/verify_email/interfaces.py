"""Business boundary for verify_email."""

from typing import Protocol

from app.users.verify_email.dto import VerifyEmailRequest


class VerifyEmailServiceInterface(Protocol):
    def execute(self, payload: VerifyEmailRequest) -> None: ...
