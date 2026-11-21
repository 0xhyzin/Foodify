"""Boundary for kitchen order preparation."""

from typing import Protocol

from app.infrastructure.models import User
from app.orders.get_order.dto import GetOrderResponse

from .dto import KitchenOrderStatusRequest


class KitchenUpdateStatusServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: KitchenOrderStatusRequest
    ) -> GetOrderResponse: ...
