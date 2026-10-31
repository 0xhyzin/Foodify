"""Application service contract."""

from typing import Protocol

from app.cart.remove_item.dto import CartResponse


class RemoveCartItemServiceInterface(Protocol):
    def execute(self, user_id: str, restaurant_id: str, cart_item_id: str) -> CartResponse: ...
