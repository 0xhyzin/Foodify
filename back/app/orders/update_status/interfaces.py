from typing import Protocol

from app.infrastructure.models import User

from .dto import GetOrderResponse, UpdateOrderStatusRequest


class UpdateOrderStatusServiceInterface(Protocol):
    def execute(
        self, actor: User, order_id: str, payload: UpdateOrderStatusRequest
    ) -> GetOrderResponse: ...
