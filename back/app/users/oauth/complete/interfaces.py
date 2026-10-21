"""Business boundary for OAuth complete."""

from typing import Protocol

from app.users.oauth.complete.dto import CompleteOAuthRequest, CompleteOAuthResponse


class CompleteOAuthServiceInterface(Protocol):
    def execute(self, payload: CompleteOAuthRequest) -> CompleteOAuthResponse: ...
