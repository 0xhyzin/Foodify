"""UpdateCartItem request and response contract."""

from app.ordering.shared.dto import CartResponse, Quantity
from app.shared.dto import APIModel


class UpdateCartItemRequest(APIModel):
    quantity: Quantity


__all__ = ["CartResponse"]
