"""Create or retrieve the authenticated user's single persistent cart."""

from typing import Protocol

from app.cart.create_cart.dto import CartResponse


class CreateCartServiceInterface(Protocol):
    def execute(self, user_id: str, restaurant_id: str) -> CartResponse: ...
