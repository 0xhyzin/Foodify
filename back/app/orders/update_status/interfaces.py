from typing import Protocol

from .dto import GetOrderResponse, UpdateOrderStatusRequest


class UpdateOrderStatusServiceInterface(Protocol):
    def execute(
        self, actor_id: str, order_id: str, payload: UpdateOrderStatusRequest
    ) -> GetOrderResponse: ...
