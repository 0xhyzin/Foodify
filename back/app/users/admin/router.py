"""Admin staff directory, onboarding, and role-update routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import (
    AdminUserListResponse,
    AdminUserResponse,
    CreateStaffRequest,
    UpdateUserRolesRequest,
)
from .interfaces import AdminUsersServiceInterface

router = APIRouter(prefix="/admin", tags=["Admin"])
Service = Annotated[AdminUsersServiceInterface, Depends(get_service)]


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    _actor: Annotated[User, Depends(require_permission("staff:read"))],
    service: Service,
    role: Annotated[str | None, Query(max_length=40)] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> AdminUserListResponse:
    return service.list_users(role, search, limit, offset)


@router.post("/staff", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_staff_account(
    payload: CreateStaffRequest,
    _actor: Annotated[User, Depends(require_permission("staff:manage"))],
    service: Service,
) -> AdminUserResponse:
    return service.create_staff(payload)


@router.patch("/users/{user_id}/roles", response_model=AdminUserResponse)
def update_user_roles(
    user_id: UUID,
    payload: UpdateUserRolesRequest,
    actor: Annotated[User, Depends(require_permission("roles:manage"))],
    service: Service,
) -> AdminUserResponse:
    return service.update_roles(actor, str(user_id), payload)
