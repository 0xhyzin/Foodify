from typing import Protocol

from app.orders.get_order.dto import GetOrderResponse
from app.payments.shared.dto import TransferClaim


class ClaimTransferServiceInterface(Protocol):
    def execute(self, user_id: str, order_id: str, payload: TransferClaim) -> GetOrderResponse: ...
