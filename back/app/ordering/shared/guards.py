"""Catalog and operational scoping invariants used by ordering operations."""

from app.infrastructure.models import User
from app.ordering.models import Restaurant
from app.ordering.shared.interfaces import CatalogRepository, RestaurantStaffRepository
from app.shared.errors import AppError


def require_restaurant(
    catalog: CatalogRepository, restaurant_id: str, for_update: bool = False
) -> Restaurant:
    restaurant = catalog.get_restaurant(restaurant_id, for_update=for_update)
    if restaurant is None or not restaurant.is_active:
        raise AppError("restaurant_not_found", "Restaurant not found or unavailable.", 404)
    return restaurant


def is_global_operator(user: User) -> bool:
    return any(role.code in {"admin", "operations_manager"} for role in user.roles)


def assert_can_manage_restaurant(
    user: User, restaurant_id: str, staff: RestaurantStaffRepository
) -> None:
    if is_global_operator(user):
        return
    if not staff.is_assigned(restaurant_id, user.id):
        raise AppError(
            "permission_denied",
            "You can only manage orders for your assigned restaurant.",
            403,
        )
