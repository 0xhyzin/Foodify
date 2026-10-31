"""Application service contract."""

from typing import Protocol

from app.cart.update_item.dto import CartResponse, UpdateCartItemRequest


class UpdateCartItemServiceInterface(Protocol):
    def execute(
        self, user_id: str, restaurant_id: str, cart_item_id: str, payload: UpdateCartItemRequest
    ) -> CartResponse: ...
