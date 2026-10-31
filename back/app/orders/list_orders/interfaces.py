"""Order operation boundary."""

from typing import Protocol

from app.orders.list_orders.dto import OrderListQuery, OrderListResponse


class ListOrdersServiceInterface(Protocol):
    def execute(self, user_id: str, query: OrderListQuery) -> OrderListResponse: ...
