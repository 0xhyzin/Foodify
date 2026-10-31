from typing import Protocol

from app.payments.shared.dto import StartPaymentResponse


class StartPaymentServiceInterface(Protocol):
    def execute(self, user_id: str, order_id: str) -> StartPaymentResponse: ...
