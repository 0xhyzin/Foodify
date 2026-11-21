"""Boundary for assigning a courier to an order."""

from typing import Protocol

from app.infrastructure.models import User

from .dto import AssignDeliveryRequest, AssignDeliveryResponse


class AssignDeliveryServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: AssignDeliveryRequest
    ) -> AssignDeliveryResponse: ...
