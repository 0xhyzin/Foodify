"""Password and token adapters behind the application security ports."""

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import Settings
from app.shared.errors import AppError
from app.shared.ports import AccessClaims


class Argon2PasswordHasher:
    def __init__(self) -> None:
        # Argon2id defaults currently use 64 MiB memory, 3 iterations, 4 lanes.
        self._hasher = Argon2Hasher(time_cost=3, memory_cost=65536, parallelism=4)

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False


class JwtTokenCodec:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def encode_access(self, user_id: str, session_id: str) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        seconds = self._settings.access_token_minutes * 60
        payload = {
            "sub": user_id,
            "sid": session_id,
            "jti": secrets.token_urlsafe(24),
            "type": "access",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(seconds=seconds),
            "iss": self._settings.jwt_issuer,
            "aud": self._settings.jwt_audience,
        }
        encoded = jwt.encode(
            payload,
            self._settings.jwt_secret.get_secret_value(),
            algorithm=self._settings.jwt_algorithm,
        )
        return encoded, seconds

    def decode_access(self, token: str) -> AccessClaims:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret.get_secret_value(),
                algorithms=[self._settings.jwt_algorithm],
                issuer=self._settings.jwt_issuer,
                audience=self._settings.jwt_audience,
                options={
                    "require": ["sub", "sid", "jti", "type", "iat", "nbf", "exp", "iss", "aud"]
                },
                leeway=5,
            )
            if (
                payload.get("type") != "access"
                or not isinstance(payload["sub"], str)
                or not isinstance(payload["sid"], str)
                or not payload["sub"]
                or not payload["sid"]
            ):
                raise ValueError("Invalid access token claims.")
            return AccessClaims(user_id=payload["sub"], session_id=payload["sid"])
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError) as exc:
            raise AppError("invalid_token", "The access token is invalid or expired.", 401) from exc
