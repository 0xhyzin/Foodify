"""Public factories used by each operation's local composition module."""

from app.users.shared.dependencies.repositories import (
    get_action_repository,
    get_address_repository,
    get_session_repository,
    get_social_repository,
    get_user_repository,
)
from app.users.shared.dependencies.resources import (
    DB,
    get_dummy_hash,
    get_email_sender,
    get_oauth_gateway,
    get_password_hasher,
    get_rate_limiter,
    get_token_codec,
    get_unit_of_work,
)
from app.users.shared.dependencies.services import (
    get_access_authenticator,
    get_email_actions,
    get_session_issuer,
)

__all__ = [
    "DB",
    "get_access_authenticator",
    "get_action_repository",
    "get_address_repository",
    "get_dummy_hash",
    "get_email_actions",
    "get_email_sender",
    "get_oauth_gateway",
    "get_password_hasher",
    "get_rate_limiter",
    "get_session_issuer",
    "get_session_repository",
    "get_social_repository",
    "get_token_codec",
    "get_unit_of_work",
    "get_user_repository",
]
