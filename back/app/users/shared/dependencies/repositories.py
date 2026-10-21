"""Request-scoped adapters share the same MySQL session."""

from app.users.shared.dependencies.resources import DB
from app.users.shared.interfaces import (
    ActionTokenRepository,
    AddressRepository,
    SessionRepository,
    SocialRepository,
    UserRepository,
)
from app.users.shared.repositories.actions import SqlAlchemyActionTokenRepository
from app.users.shared.repositories.addresses import SqlAlchemyAddressRepository
from app.users.shared.repositories.sessions import SqlAlchemySessionRepository
from app.users.shared.repositories.social import SqlAlchemySocialRepository
from app.users.shared.repositories.users import SqlAlchemyUserRepository


def get_user_repository(db: DB) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def get_address_repository(db: DB) -> AddressRepository:
    return SqlAlchemyAddressRepository(db)


def get_action_repository(db: DB) -> ActionTokenRepository:
    return SqlAlchemyActionTokenRepository(db)


def get_session_repository(db: DB) -> SessionRepository:
    return SqlAlchemySessionRepository(db)


def get_social_repository(db: DB) -> SocialRepository:
    return SqlAlchemySocialRepository(db)
