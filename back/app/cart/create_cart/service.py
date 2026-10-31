"""Explicit cart creation preserves any existing items and serializes first creation."""

from app.cart.create_cart.dto import CartResponse
from app.ordering.shared.cart_state import lock_cart, present_cart
from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CartRepository, CatalogRepository
from app.shared.ports import UnitOfWork
from app.users.shared.interfaces import UserRepository


class CreateCartService:
    def __init__(
        self,
        users: UserRepository,
        carts: CartRepository,
        catalog: CatalogRepository,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.carts, self.catalog, self.uow = users, carts, catalog, uow

    def execute(self, user_id: str, restaurant_id: str) -> CartResponse:
        require_restaurant(self.catalog, restaurant_id)
        cart = lock_cart(self.users, self.carts, self.uow, user_id, restaurant_id)
        response = present_cart(self.catalog, cart, for_update=True)
        self.uow.commit()
        return response
