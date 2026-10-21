"""Shared resource factories; no login/register/profile orchestration."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import Argon2PasswordHasher, JwtTokenCodec
from app.infrastructure.database import get_db
from app.infrastructure.oauth import SocialOAuthGateway
from app.infrastructure.outbox import OutboxEmailSender
from app.infrastructure.rate_limit import RedisRateLimiter
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.ports import EmailSender, PasswordHasher, TokenCodec, UnitOfWork
from app.shared.tokens import generate_token

DB = Annotated[Session, Depends(get_db)]


@lru_cache(maxsize=1)
def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


@lru_cache(maxsize=1)
def get_dummy_hash() -> str:
    return get_password_hasher().hash(generate_token())


@lru_cache(maxsize=1)
def get_token_codec() -> TokenCodec:
    return JwtTokenCodec(get_settings())


@lru_cache(maxsize=1)
def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(get_settings())


@lru_cache(maxsize=1)
def get_oauth_gateway() -> SocialOAuthGateway:
    return SocialOAuthGateway(get_settings())


def get_unit_of_work(db: DB) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(db)


def get_email_sender(db: DB) -> EmailSender:
    return OutboxEmailSender(db, get_settings())
