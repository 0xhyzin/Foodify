"""AddCartItem request and response contract."""

from uuid import UUID

from app.ordering.shared.dto import CartResponse, Quantity
from app.shared.dto import APIModel


class AddCartItemRequest(APIModel):
    menu_item_id: UUID
    quantity: Quantity = 1


__all__ = ["CartResponse"]
