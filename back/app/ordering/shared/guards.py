"""Catalog invariants used by cart and checkout operations."""

from app.ordering.models import Restaurant
from app.ordering.shared.interfaces import CatalogRepository
from app.shared.errors import AppError


def require_restaurant(
    catalog: CatalogRepository, restaurant_id: str, for_update: bool = False
) -> Restaurant:
    restaurant = catalog.get_restaurant(restaurant_id, for_update=for_update)
    if restaurant is None or not restaurant.is_active:
        raise AppError("restaurant_not_found", "Restaurant not found or unavailable.", 404)
    return restaurant
