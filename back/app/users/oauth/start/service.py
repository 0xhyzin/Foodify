"""Only the OAuth start business use case."""

import secrets
from datetime import timedelta

from app.infrastructure.models import OAuthState
from app.shared.ports import OAuthGateway, UnitOfWork
from app.shared.time import utcnow
from app.shared.tokens import generate_token, hash_token
from app.users.oauth.start.dto import StartOAuthRequest, StartOAuthResponse
from app.users.shared.interfaces import (
    SocialRepository,
)


class StartOAuthService:
    def __init__(
        self, social: SocialRepository, gateway: OAuthGateway, uow: UnitOfWork, state_minutes: int
    ) -> None:
        self.social = social
        self.gateway = gateway
        self.uow = uow
        self.state_minutes = state_minutes

    def execute(self, provider: str, payload: StartOAuthRequest) -> StartOAuthResponse:
        binding_challenge = payload.binding_challenge
        state, verifier, nonce = generate_token(), secrets.token_urlsafe(64), generate_token()
        url = self.gateway.authorization_url(provider, state, verifier, nonce)
        self.social.add_state(
            OAuthState(
                state_hash=hash_token(state),
                provider=provider,
                code_verifier=verifier,
                nonce=nonce,
                binding_hash=hash_token(binding_challenge),
                expires_at=utcnow() + timedelta(minutes=self.state_minutes),
            )
        )
        self.uow.commit()
        return StartOAuthResponse(authorization_url=url)
