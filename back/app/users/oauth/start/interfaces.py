"""Business boundary for OAuth start."""

from typing import Protocol

from app.users.oauth.start.dto import StartOAuthRequest, StartOAuthResponse


class StartOAuthServiceInterface(Protocol):
    def execute(self, provider: str, payload: StartOAuthRequest) -> StartOAuthResponse: ...
