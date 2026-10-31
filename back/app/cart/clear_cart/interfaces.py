"""Application service contract."""

from typing import Protocol

from app.cart.clear_cart.dto import CartResponse


class ClearCartServiceInterface(Protocol):
    def execute(self, user_id: str, restaurant_id: str) -> CartResponse: ...
