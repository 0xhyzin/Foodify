from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.ordering.models import FoodOrder


@dataclass(frozen=True)
class HostedCheckout:
    provider_order_id: str
    intention_id: str
    encrypted_token: str
    expires_at: datetime
    url: str


@dataclass(frozen=True)
class VerifiedTransaction:
    id: str
    provider_order_id: str
    amount_cents: int
    currency: str
    integration_id: int
    status: str


class HostedPaymentGateway(Protocol):
    def create_checkout(self, order: FoodOrder, email: str) -> HostedCheckout: ...
    def checkout_url(self, encrypted_token: str) -> str: ...
    def verify_callback(self, payload: dict, signature: str) -> VerifiedTransaction: ...
    def integration_id(self, method: str) -> int: ...


class PaymentMethods(Protocol):
    def methods(self) -> list[dict]: ...
