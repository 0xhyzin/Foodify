from typing import Literal

from pydantic import Field

from app.orders.get_order.dto import GetOrderResponse
from app.shared.dto import APIModel


class UpdateOrderStatusRequest(APIModel):
    status: Literal["preparing", "ready", "out_for_delivery", "delivered"]
    note: str | None = Field(default=None, max_length=250)


__all__ = ["GetOrderResponse"]
