"""Application service contract."""

from typing import Protocol

from app.cart.add_item.dto import AddCartItemRequest, CartResponse


class AddCartItemServiceInterface(Protocol):
    def execute(
        self, user_id: str, restaurant_id: str, payload: AddCartItemRequest
    ) -> CartResponse: ...
