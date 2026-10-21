"""Validate customer credentials and open one authenticated session."""

from app.shared.errors import AppError
from app.shared.ports import PasswordHasher, UnitOfWork
from app.users.login.dto import LoginRequest, LoginResponse
from app.users.shared.interfaces import SessionIssuerInterface, UserRepository


class LoginService:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        session_issuer: SessionIssuerInterface,
        uow: UnitOfWork,
        dummy_password_hash: str,
    ) -> None:
        self.users = users
        self.hasher = hasher
        self.session_issuer = session_issuer
        self.uow = uow
        self.dummy_password_hash = dummy_password_hash

    def execute(self, payload: LoginRequest) -> LoginResponse:
        user = self.users.get_by_email(payload.email)
        old_hash = user.password_hash if user and user.password_hash else self.dummy_password_hash
        valid = self.hasher.verify(payload.password, old_hash)
        if user is None or not user.is_active or not user.password_hash or not valid:
            raise AppError("invalid_credentials", "Email or password is incorrect.", 401)
        user = self.users.get_by_id(user.id, for_update=True)
        # A concurrent password reset can complete while verification is running.
        if user is None or not user.is_active or user.password_hash != old_hash:
            raise AppError("invalid_credentials", "Email or password is incorrect.", 401)
        if not user.is_email_verified:
            raise AppError(
                "email_verification_required", "Confirm your email before signing in.", 403
            )
        response = self.session_issuer.create_session(user)
        self.uow.commit()
        return LoginResponse.model_validate(response)
