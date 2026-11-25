"""Application service for admin staff onboarding, listing, and role management."""

from app.infrastructure.models import User
from app.ordering.shared.dto import Pagination
from app.ordering.shared.interfaces import CatalogRepository, RestaurantStaffRepository
from app.roles.enums import RoleType
from app.shared.errors import AppError
from app.shared.ports import PasswordHasher, UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import SessionRepository, UserRepository

from .dto import (
    AdminUserData,
    AdminUserListData,
    AdminUserListResponse,
    AdminUserResponse,
    CreateStaffRequest,
    UpdateUserRolesRequest,
    admin_user_view,
)
from .interfaces import AdminDirectoryRepository

STAFF_LINKABLE_ROLES = frozenset(
    {RoleType.RESTAURANT_MANAGER, RoleType.ORDER_PREPARER}
)


class AdminUsersService:
    def __init__(
        self,
        users: UserRepository,
        directory: AdminDirectoryRepository,
        catalog: CatalogRepository,
        staff: RestaurantStaffRepository,
        sessions: SessionRepository,
        hasher: PasswordHasher,
        uow: UnitOfWork,
    ) -> None:
        self.users = users
        self.directory = directory
        self.catalog = catalog
        self.staff = staff
        self.sessions = sessions
        self.hasher = hasher
        self.uow = uow

    def _resolve_roles(self, role_types: list[RoleType]):
        codes = list(dict.fromkeys(str(item) for item in role_types))
        roles = self.directory.get_roles_by_codes(codes)
        if len(roles) != len(codes):
            raise AppError("role_not_found", "One or more requested roles do not exist.", 400)
        return roles

    def list_users(
        self, role: str | None, search: str | None, limit: int, offset: int
    ) -> AdminUserListResponse:
        items = self.directory.list_users(role, search, limit + 1, offset)
        visible = items[:limit]
        staff_map = self.directory.list_managed_restaurant_map([u.id for u in visible])
        return AdminUserListResponse(
            data=AdminUserListData(
                users=[admin_user_view(u, staff_map.get(u.id, [])) for u in visible],
                pagination=Pagination(
                    limit=limit, offset=offset, has_more=len(items) > limit
                ),
            )
        )

    def create_staff(self, payload: CreateStaffRequest) -> AdminUserResponse:
        if self.users.get_by_email(payload.email) is not None:
            raise AppError(
                "email_already_registered", "Email is already registered.", 409
            )
        roles = self._resolve_roles(payload.roles)
        restaurant_id = str(payload.restaurant_id) if payload.restaurant_id else None
        if restaurant_id is not None:
            if self.catalog.get_restaurant(restaurant_id) is None:
                raise AppError("restaurant_not_found", "Restaurant not found.", 404)

        user = User(
            name=payload.name.strip(),
            email=payload.email,
            phone=payload.phone,
            password_hash=self.hasher.hash(payload.password),
            is_email_verified=True,
            is_active=True,
            created_at=utcnow(),
            roles=roles,
        )
        self.users.add(user)
        self.uow.flush()

        linked_ids: list[str] = []
        if restaurant_id is not None and any(r in STAFF_LINKABLE_ROLES for r in payload.roles):
            self.staff.assign_staff(restaurant_id, user.id)
            linked_ids.append(restaurant_id)
            self.uow.flush()

        response = AdminUserResponse(
            data=AdminUserData(user=admin_user_view(user, linked_ids))
        )
        self.uow.commit()
        return response

    def update_roles(
        self, actor: User, user_id: str, payload: UpdateUserRolesRequest
    ) -> AdminUserResponse:
        target = self.users.get_by_id(user_id, for_update=True)
        if target is None:
            raise AppError("staff_user_not_found", "User not found.", 404)
        if target.id == actor.id and (
            RoleType.ADMIN not in payload.roles or payload.is_active is False
        ):
            raise AppError(
                "cannot_demote_self",
                "Administrators cannot remove their own admin access or deactivate themselves.",
                409,
            )

        roles = self._resolve_roles(payload.roles)
        target.roles = roles
        if payload.is_active is not None:
            target.is_active = payload.is_active
            if payload.is_active is False:
                self.sessions.revoke_all(target.id)

        restaurant_id = str(payload.restaurant_id) if payload.restaurant_id else None
        if restaurant_id is not None:
            if self.catalog.get_restaurant(restaurant_id) is None:
                raise AppError("restaurant_not_found", "Restaurant not found.", 404)
            if any(r in STAFF_LINKABLE_ROLES for r in payload.roles):
                self.staff.assign_staff(restaurant_id, target.id)

        self.uow.flush()
        managed = self.directory.list_managed_restaurant_map([target.id]).get(
            target.id, []
        )
        response = AdminUserResponse(data=AdminUserData(user=admin_user_view(target, managed)))
        self.uow.commit()
        return response
