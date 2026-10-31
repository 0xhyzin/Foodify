"""RemoveCartItem use case; shared parent lock serializes cart mutations."""

from app.cart.remove_item.dto import CartResponse
from app.ordering.shared.cart_state import lock_cart, present_cart
from app.ordering.shared.interfaces import CartRepository, CatalogRepository
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository


class RemoveCartItemService:
    def __init__(
        self,
        users: UserRepository,
        carts: CartRepository,
        catalog: CatalogRepository,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.carts, self.catalog, self.uow = users, carts, catalog, uow

    def execute(self, user_id: str, restaurant_id: str, cart_item_id: str) -> CartResponse:
        cart = lock_cart(self.users, self.carts, self.uow, user_id, restaurant_id)
        entry = next((line for line in cart.items if line.id == cart_item_id), None)
        if entry is None:
            raise AppError("cart_item_not_found", "Cart item not found.", 404)
        cart.items.remove(entry)
        cart.revision += 1
        cart.updated_at = utcnow()
        self.uow.flush()
        response = present_cart(self.catalog, cart, for_update=True)
        self.uow.commit()
        return response
