"""Order operation boundary."""

from typing import Protocol

from app.orders.list_restaurant_orders.dto import OrderListQuery, OrderListResponse


class ListRestaurantOrdersServiceInterface(Protocol):
    def execute(self, restaurant_id: str, query: OrderListQuery) -> OrderListResponse: ...
