"""Application service contract."""

from typing import Protocol

from app.cart.get_cart.dto import CartResponse


class GetCartServiceInterface(Protocol):
    def execute(self, user_id: str, restaurant_id: str) -> CartResponse: ...
