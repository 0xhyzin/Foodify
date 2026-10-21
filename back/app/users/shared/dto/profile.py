"""Public user representation shared by multiple operations."""

from datetime import UTC, datetime

from app.infrastructure.models import User
from app.shared.dto import APIModel


class UserResponse(APIModel):
    id: str
    name: str
    email: str
    phone: str | None
    email_verified: bool
    roles: list[str]
    permissions: list[str]
    profile_complete: bool
    default_address_id: str | None
    created_at: datetime


def _as_utc(value: datetime) -> datetime:
    """MySQL stores naive UTC; API timestamps carry an explicit UTC offset."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        email_verified=user.is_email_verified,
        roles=sorted(role.code for role in user.roles),
        permissions=sorted(
            {permission.code for role in user.roles for permission in role.permissions}
        ),
        profile_complete=bool(user.phone and user.default_address_id),
        default_address_id=user.default_address_id,
        created_at=_as_utc(user.created_at),
    )
