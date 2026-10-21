"""Only the OAuth callback business use case."""

from datetime import timedelta

from pydantic import ValidationError

from app.infrastructure.models import OAuthTicket, SocialAccount, User, new_id
from app.shared.errors import AppError, PersistenceConflict
from app.shared.ports import OAuthGateway, UnitOfWork
from app.shared.time import utcnow
from app.shared.tokens import generate_token, hash_token
from app.users.oauth.callback.dto import OAuthCallbackRequest, OAuthCallbackResult
from app.users.shared.dto.credentials import EmailRequest
from app.users.shared.interfaces import (
    ActionTokenRepository,
    EmailActionServiceInterface,
    SocialRepository,
    UserRepository,
)


class OAuthCallbackService:
    def __init__(
        self,
        users: UserRepository,
        social: SocialRepository,
        actions: ActionTokenRepository,
        gateway: OAuthGateway,
        email_actions: EmailActionServiceInterface,
        uow: UnitOfWork,
    ) -> None:
        self.users = users
        self.social = social
        self.actions = actions
        self.gateway = gateway
        self.email_actions = email_actions
        self.uow = uow

    def execute(self, provider: str, payload: OAuthCallbackRequest) -> OAuthCallbackResult:
        state, code, error = payload.state, payload.code, payload.error
        attempt = self.social.get_state(hash_token(state))
        if (
            attempt is None
            or attempt.provider != provider
            or attempt.consumed_at is not None
            or attempt.expires_at <= utcnow()
        ):
            raise AppError("invalid_oauth_state", "Social sign-in expired. Start again.", 400)
        attempt.consumed_at = utcnow()
        # Release lock before provider network calls; a code is attempted once.
        self.uow.commit()
        if error or not code:
            raise AppError("oauth_cancelled", "Social sign-in was cancelled. Start again.", 400)
        identity = self.gateway.exchange_identity(
            provider, code, attempt.code_verifier, attempt.nonce
        )
        if identity.provider != provider:
            raise AppError("oauth_failed", "Social sign-in could not be completed.", 401)
        account = self.social.find_account(provider, identity.subject)
        if account:
            user = self.users.get_by_id(account.user_id, for_update=True)
            if user is None or not user.is_active:
                raise AppError("oauth_failed", "Social sign-in could not be completed.", 401)
        else:
            if not identity.email:
                raise AppError(
                    "oauth_email_required",
                    "Your provider must supply an email address. Register with email instead.",
                    400,
                )
            try:
                email = EmailRequest(email=identity.email).email
            except ValidationError as exc:
                raise AppError(
                    "oauth_email_required",
                    "Your provider did not supply a valid email address.",
                    400,
                ) from exc
            # An email match alone cannot attach a social identity to an account.
            if self.users.get_by_email(email) is not None:
                raise AppError(
                    "oauth_account_link_required",
                    "Use your original sign-in method for this account.",
                    409,
                )
            user = User(
                id=new_id(),
                name=identity.display_name.strip()[:100] or "Customer",
                email=email,
                password_hash=None,
                is_active=True,
                is_email_verified=identity.email_verified,
                created_at=utcnow(),
                roles=[self.actions.get_customer_role()],
            )
            self.users.add(user)
            try:
                self.uow.flush()
                self.social.add_account(
                    SocialAccount(
                        id=new_id(),
                        user_id=user.id,
                        provider=provider,
                        provider_subject=identity.subject,
                    )
                )
                if not user.is_email_verified:
                    self.email_actions.queue_email_action(user, "verify_email")
                self.uow.flush()
            except PersistenceConflict as exc:
                self.uow.rollback()
                raise AppError(
                    "oauth_failed", "Social sign-in changed concurrently. Start again.", 409
                ) from exc
        if not user.is_email_verified:
            self.uow.commit()
            return OAuthCallbackResult(fragment="error=email_verification_required")
        raw_ticket = generate_token()
        self.social.add_ticket(
            OAuthTicket(
                ticket_hash=hash_token(raw_ticket),
                user_id=user.id,
                binding_hash=attempt.binding_hash,
                expires_at=utcnow() + timedelta(minutes=2),
            )
        )
        self.uow.commit()
        return OAuthCallbackResult(fragment=f"ticket={raw_ticket}")
