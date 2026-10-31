"""Small shared cart invariants; operations keep their own orchestration."""

from app.ordering.models import Cart
from app.ordering.shared.dto import CartResponse
from app.ordering.shared.interfaces import CartRepository, CatalogRepository
from app.ordering.shared.mappers import cart_response
from app.ordering.shared.pricing import ZERO
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import UserRepository


def lock_cart(
    users: UserRepository, carts: CartRepository, uow: UnitOfWork, user_id: str, restaurant_id: str
) -> Cart:
    # Same parent lock as address changes; serializes first cart creation and checkout.
    require_active_user(users, user_id, for_update=True)
    cart = carts.get_for_user(user_id, restaurant_id, for_update=True)
    if cart is None:
        cart = Cart(user_id=user_id, restaurant_id=restaurant_id, revision=0, items=[])
        carts.add(cart)
        uow.flush()
    return cart


def load_cart_menu(catalog: CatalogRepository, cart: Cart, for_update: bool = False) -> None:
    # Stable order reduces contention; locking reads see current prices under MySQL RR.
    menus = {
        menu.id: menu
        for menu in catalog.get_menu_items(
            [entry.menu_item_id for entry in cart.items], for_update=for_update
        )
    }
    for entry in cart.items:
        menu = menus.get(entry.menu_item_id)
        if menu is None or menu.restaurant_id != cart.restaurant_id:
            raise AppError("cart_inconsistent", "Clear the cart and add your items again.", 409)
        entry.menu_item = menu


def present_cart(
    catalog: CatalogRepository, cart: Cart | None, for_update: bool = False
) -> CartResponse:
    if cart is None or not cart.items:
        return cart_response(cart)
    restaurant = catalog.get_restaurant(cart.restaurant_id, for_update=for_update)
    load_cart_menu(catalog, cart, for_update=for_update)
    return cart_response(
        cart,
        restaurant.delivery_fee if restaurant else ZERO,
        restaurant_active=bool(restaurant and restaurant.is_active),
    )
