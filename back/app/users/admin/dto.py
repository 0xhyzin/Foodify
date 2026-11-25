"""DTO contracts for platform admin user directory and staff onboarding."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from app.infrastructure.models import User
from app.ordering.shared.dto import Pagination
from app.roles.enums import RoleType
from app.shared.dto import APIModel
from app.users.shared.dto.credentials import EmailRequest, Password
from app.users.shared.dto.primitives import PersonName, PhoneNumber


class AdminUserView(APIModel):
    id: str
    name: str
    email: str
    phone: str | None
    is_active: bool
    email_verified: bool
    roles: list[str]
    managed_restaurant_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class CreateStaffRequest(EmailRequest):
    name: PersonName
    password: Password
    phone: PhoneNumber | None = None
    roles: list[RoleType] = Field(min_length=1, max_length=6)
    restaurant_id: UUID | None = None


class UpdateUserRolesRequest(APIModel):
    roles: list[RoleType] = Field(min_length=1, max_length=6)
    is_active: bool | None = None
    email_verified: bool | None = None
    restaurant_id: UUID | None = None


class AdminUserData(APIModel):
    user: AdminUserView


class AdminUserResponse(APIModel):
    data: AdminUserData


class AdminUserListData(APIModel):
    users: list[AdminUserView]
    pagination: Pagination


class AdminUserListResponse(APIModel):
    data: AdminUserListData


def admin_user_view(
    user: User, managed_restaurant_ids: list[str] | None = None
) -> AdminUserView:
    return AdminUserView(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        email_verified=user.is_email_verified,
        roles=[role.code for role in user.roles],
        managed_restaurant_ids=managed_restaurant_ids or [],
        created_at=user.created_at.replace(tzinfo=UTC),
    )
