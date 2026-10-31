from typing import Protocol

from app.orders.get_order.dto import GetOrderResponse
from app.payments.shared.dto import TransferReview


class ReviewTransferServiceInterface(Protocol):
    def execute(
        self, actor_id: str, order_id: str, payload: TransferReview
    ) -> GetOrderResponse: ...
