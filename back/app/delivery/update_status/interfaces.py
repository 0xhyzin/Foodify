"""Boundary for courier pickup/delivery status updates."""

from typing import Protocol

from app.infrastructure.models import User

from .dto import UpdateDeliveryStatusRequest, UpdateDeliveryStatusResponse


class UpdateDeliveryStatusServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: UpdateDeliveryStatusRequest
    ) -> UpdateDeliveryStatusResponse: ...
