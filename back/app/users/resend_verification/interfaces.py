"""Business boundary for resend_verification."""

from typing import Protocol

from app.users.resend_verification.dto import ResendVerificationRequest


class ResendVerificationServiceInterface(Protocol):
    def execute(self, payload: ResendVerificationRequest) -> None: ...
