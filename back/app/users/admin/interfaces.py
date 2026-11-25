"""Service and directory interfaces for Admin staff operations."""

from typing import Protocol

from app.infrastructure.models import Role, User

from .dto import (
    AdminUserListResponse,
    AdminUserResponse,
    CreateStaffRequest,
    UpdateUserRolesRequest,
)


class AdminDirectoryRepository(Protocol):
    def list_users(
        self, role_code: str | None, search: str | None, limit: int, offset: int
    ) -> list[User]: ...

    def get_roles_by_codes(self, codes: list[str]) -> list[Role]: ...

    def list_managed_restaurant_map(self, user_ids: list[str]) -> dict[str, list[str]]: ...


class AdminUsersServiceInterface(Protocol):
    def list_users(
        self, role: str | None, search: str | None, limit: int, offset: int
    ) -> AdminUserListResponse: ...

    def create_staff(self, payload: CreateStaffRequest) -> AdminUserResponse: ...

    def update_roles(
        self, actor: User, user_id: str, payload: UpdateUserRolesRequest
    ) -> AdminUserResponse: ...
