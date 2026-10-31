"""Checkout only accepts owned address IDs and an explicit simulation method."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.ordering.shared.dto import OrderView
from app.shared.dto import APIModel


class CheckoutRequest(APIModel):
    restaurant_id: UUID
    address_id: UUID
    payment_method: Literal[
        "card", "vodafone_cash", "orange_cash", "instapay", "cash", "simulated", "sandbox"
    ]
    expected_total: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    cart_revision: int = Field(ge=0, strict=True)


class CheckoutData(APIModel):
    order: OrderView
    confirmation: str
    is_replay: bool


class CheckoutResponse(APIModel):
    data: CheckoutData
