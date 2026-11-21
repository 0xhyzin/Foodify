"""Cancellation payload contract."""

from pydantic import Field

from app.orders.get_order.dto import GetOrderResponse
from app.shared.dto import APIModel


class CancelOrderRequest(APIModel):
    note: str | None = Field(default=None, max_length=250)


__all__ = ["CancelOrderRequest", "GetOrderResponse"]
