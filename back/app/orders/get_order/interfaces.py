"""Order operation boundary."""

from typing import Protocol

from app.orders.get_order.dto import GetOrderResponse


class GetOrderServiceInterface(Protocol):
    def execute(self, user_id: str, order_id: str) -> GetOrderResponse: ...
