"""Read the authenticated user's cart without creating or mutating storage."""

from app.cart.get_cart.dto import CartResponse
from app.ordering.shared.cart_state import present_cart
from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CartRepository, CatalogRepository


class GetCartService:
    def __init__(self, carts: CartRepository, catalog: CatalogRepository) -> None:
        self.carts, self.catalog = carts, catalog

    def execute(self, user_id: str, restaurant_id: str) -> CartResponse:
        require_restaurant(self.catalog, restaurant_id)
        response = present_cart(self.catalog, self.carts.get_for_user(user_id, restaurant_id))
        response.data.cart.restaurant_id = restaurant_id
        return response
