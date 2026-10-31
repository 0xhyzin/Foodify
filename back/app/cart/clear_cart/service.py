"""ClearCart use case; shared parent lock serializes cart mutations."""

from app.cart.clear_cart.dto import CartResponse
from app.ordering.shared.cart_state import lock_cart
from app.ordering.shared.interfaces import CartRepository, CatalogRepository
from app.ordering.shared.mappers import cart_response
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository


class ClearCartService:
    def __init__(
        self,
        users: UserRepository,
        carts: CartRepository,
        catalog: CatalogRepository,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.carts, self.catalog, self.uow = users, carts, catalog, uow

    def execute(self, user_id: str, restaurant_id: str) -> CartResponse:
        cart = lock_cart(self.users, self.carts, self.uow, user_id, restaurant_id)
        cart.items.clear()
        cart.revision += 1
        cart.updated_at = utcnow()
        self.uow.flush()
        response = cart_response(cart)
        self.uow.commit()
        return response
