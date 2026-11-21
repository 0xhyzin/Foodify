"""Boundary for browser email confirmation and session creation."""

from typing import Protocol

from app.users.shared.dto.tokens import TokenResponse
from app.users.verify_email.dto import VerifyEmailRequest


class VerifyBrowserEmailServiceInterface(Protocol):
    def execute(self, payload: VerifyEmailRequest) -> TokenResponse: ...
