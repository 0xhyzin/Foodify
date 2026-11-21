"""Boundary for assigning an order preparer."""

from typing import Protocol

from app.infrastructure.models import User
from app.orders.get_order.dto import GetOrderResponse

from .dto import AssignPreparerRequest


class AssignPreparerServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: AssignPreparerRequest
    ) -> GetOrderResponse: ...
