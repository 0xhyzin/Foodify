"""Boundary for order cancellation."""

from typing import Protocol

from app.infrastructure.models import User

from .dto import CancelOrderRequest, GetOrderResponse


class CancelOrderServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: CancelOrderRequest
    ) -> GetOrderResponse: ...
