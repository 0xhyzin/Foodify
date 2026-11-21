"""Order operation boundary."""

from typing import Protocol

from app.infrastructure.models import User
from app.orders.list_restaurant_orders.dto import OrderListQuery, OrderListResponse


class ListRestaurantOrdersServiceInterface(Protocol):
    def execute(
        self, actor: User, restaurant_id: str, query: OrderListQuery
    ) -> OrderListResponse: ...
