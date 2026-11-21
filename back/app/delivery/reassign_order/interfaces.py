"""Boundary for reassigning an order's courier."""

from typing import Protocol

from app.infrastructure.models import User

from .dto import ReassignDeliveryRequest, ReassignDeliveryResponse


class ReassignDeliveryServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: ReassignDeliveryRequest
    ) -> ReassignDeliveryResponse: ...
