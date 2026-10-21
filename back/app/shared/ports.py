"""Replaceable boundaries used by application services."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AccessClaims:
    user_id: str
    session_id: str


@dataclass(frozen=True)
class OAuthIdentity:
    provider: str
    subject: str
    email: str | None
    email_verified: bool
    display_name: str


class UnitOfWork(Protocol):
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenCodec(Protocol):
    def encode_access(self, user_id: str, session_id: str) -> tuple[str, int]: ...
    def decode_access(self, token: str) -> AccessClaims: ...


class EmailSender(Protocol):
    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None: ...


class RateLimiter(Protocol):
    def check(self, scope: str, key: str, limit: int, window_seconds: int) -> None: ...


class OAuthGateway(Protocol):
    def authorization_url(
        self, provider: str, state: str, code_verifier: str, nonce: str
    ) -> str: ...
    def exchange_identity(
        self, provider: str, code: str, code_verifier: str, nonce: str
    ) -> OAuthIdentity: ...
