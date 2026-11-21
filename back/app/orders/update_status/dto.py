from typing import Literal

from pydantic import Field

from app.orders.get_order.dto import GetOrderResponse
from app.shared.dto import APIModel


class UpdateOrderStatusRequest(APIModel):
    status: Literal[
        "accepted",
        "rejected",
        "preparing",
        "ready_for_pickup",
        "picked_up",
        "delivered",
    ]
    note: str | None = Field(default=None, max_length=250)


__all__ = ["GetOrderResponse"]
