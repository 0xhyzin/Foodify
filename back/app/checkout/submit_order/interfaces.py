"""Checkout service boundary."""

from typing import Protocol

from app.checkout.submit_order.dto import CheckoutRequest, CheckoutResponse


class CheckoutServiceInterface(Protocol):
    def execute(self, user_id: str, key: str, payload: CheckoutRequest) -> CheckoutResponse: ...
