"""Common authentication/authorization and rate-limit dependencies only."""

from typing import Annotated, Callable

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.api_docs import BEARER_DESCRIPTION, BEARER_SCHEME_NAME
from app.core.client_ip import get_client_ip
from app.infrastructure.models import User
from app.shared.errors import AppError
from app.users.shared.dependencies import get_access_authenticator, get_rate_limiter
from app.users.shared.interfaces import AccessAuthenticatorInterface

bearer_scheme = HTTPBearer(
    scheme_name=BEARER_SCHEME_NAME,
    bearerFormat="JWT",
    description=BEARER_DESCRIPTION,
    auto_error=False,
)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("authentication_required", "A Bearer access token is required.", 401)
    return credentials.credentials


def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    service: Annotated[AccessAuthenticatorInterface, Depends(get_access_authenticator)],
) -> User:
    return service.authenticate_access(token)


def require_permission(permission: str) -> Callable:
    def check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not any(
            permission == item.code for role in current_user.roles for item in role.permissions
        ):
            raise AppError("permission_denied", "You do not have permission for this action.", 403)
        return current_user

    return check


def limit_api_requests(request: Request) -> None:
    key = get_client_ip(request)
    get_rate_limiter().check("api", key, 120, 60)


def limit_auth_requests(request: Request) -> None:
    key = get_client_ip(request)
    get_rate_limiter().check("authentication", key, 30, 900)


def limit_email_action(scope: str, email: str, limit: int = 5) -> None:
    get_rate_limiter().check(scope, email, limit, 900)
