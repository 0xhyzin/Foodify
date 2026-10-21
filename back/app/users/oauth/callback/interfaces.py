"""Business boundary for OAuth callback."""

from typing import Protocol

from app.users.oauth.callback.dto import OAuthCallbackRequest, OAuthCallbackResult


class OAuthCallbackServiceInterface(Protocol):
    def execute(self, provider: str, payload: OAuthCallbackRequest) -> OAuthCallbackResult: ...
