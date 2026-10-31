"""AddCartItem use case; shared parent lock serializes cart mutations."""

from app.cart.add_item.dto import AddCartItemRequest, CartResponse
from app.ordering.models import CartItem
from app.ordering.shared.cart_state import lock_cart, present_cart
from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CartRepository, CatalogRepository
from app.ordering.shared.pricing import MAX_CART_LINES, MAX_QUANTITY
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository


class AddCartItemService:
    def __init__(
        self,
        users: UserRepository,
        carts: CartRepository,
        catalog: CatalogRepository,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.carts, self.catalog, self.uow = users, carts, catalog, uow

    def execute(
        self, user_id: str, restaurant_id: str, payload: AddCartItemRequest
    ) -> CartResponse:
        cart = lock_cart(self.users, self.carts, self.uow, user_id, restaurant_id)
        menu = self.catalog.get_menu_item(str(payload.menu_item_id))
        if menu is None or menu.restaurant_id != restaurant_id:
            raise AppError("menu_item_unavailable", "Menu item is unavailable.", 404)
        restaurant = require_restaurant(self.catalog, menu.restaurant_id, for_update=True)
        menu = self.catalog.get_menu_item(menu.id, for_update=True)
        if menu is None or not menu.is_available or menu.restaurant_id != restaurant.id:
            raise AppError("menu_item_unavailable", "Menu item is unavailable.", 409)
        existing = next((line for line in cart.items if line.menu_item_id == menu.id), None)
        if existing:
            quantity = existing.quantity + payload.quantity
            if quantity > MAX_QUANTITY:
                raise AppError("quantity_limit_exceeded", "An item can have at most 99 units.", 409)
            existing.quantity = quantity
        else:
            if len(cart.items) >= MAX_CART_LINES:
                raise AppError(
                    "cart_limit_reached", "A cart can contain up to 50 different items.", 409
                )
            cart.items.append(
                CartItem(menu_item_id=menu.id, quantity=payload.quantity, menu_item=menu)
            )
        cart.restaurant_id = restaurant.id
        cart.revision += 1
        cart.updated_at = utcnow()
        self.uow.flush()
        response = present_cart(self.catalog, cart, for_update=True)
        self.uow.commit()
        return response
