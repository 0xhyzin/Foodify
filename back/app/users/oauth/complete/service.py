"""Only the OAuth complete business use case."""

from hmac import compare_digest

from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.shared.tokens import hash_browser_binding_verifier, hash_token
from app.users.oauth.complete.dto import CompleteOAuthRequest, CompleteOAuthResponse
from app.users.shared.interfaces import SessionIssuerInterface, SocialRepository, UserRepository


class CompleteOAuthService:
    def __init__(
        self,
        users: UserRepository,
        social: SocialRepository,
        issuer: SessionIssuerInterface,
        uow: UnitOfWork,
    ) -> None:
        self.users = users
        self.social = social
        self.issuer = issuer
        self.uow = uow

    def execute(self, payload: CompleteOAuthRequest) -> CompleteOAuthResponse:
        raw_ticket, binding_verifier = payload.ticket, payload.binding_verifier
        digest = hash_token(raw_ticket)
        ticket = self.social.get_ticket(digest)
        if ticket is None:
            raise self._invalid_ticket()
        user = self.users.get_by_id(ticket.user_id, for_update=True)
        ticket = self.social.get_ticket(digest, for_update=True)
        if (
            user is None
            or not user.is_active
            or not user.is_email_verified
            or ticket is None
            or ticket.consumed_at is not None
            or ticket.expires_at <= utcnow()
            or not compare_digest(
                ticket.binding_hash, hash_browser_binding_verifier(binding_verifier)
            )
        ):
            raise self._invalid_ticket()
        ticket.consumed_at = utcnow()
        response = self.issuer.create_session(user)
        self.uow.commit()
        return CompleteOAuthResponse.model_validate(response)

    @staticmethod
    def _invalid_ticket() -> AppError:
        return AppError(
            "invalid_oauth_ticket",
            "Social sign-in expired or belongs to another browser. Start again.",
            400,
        )
