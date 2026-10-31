from datetime import datetime
from typing import Literal

from pydantic import Field

from app.shared.dto import APIModel


class PaymentMethodView(APIModel):
    code: str
    label: str
    enabled: bool
    recipient: str | None = None
    recipient_name: str | None = None


class PaymentMethodsData(APIModel):
    methods: list[PaymentMethodView]


class PaymentMethodsResponse(APIModel):
    data: PaymentMethodsData


class StartPaymentData(APIModel):
    order_id: str
    checkout_url: str
    expires_at: datetime


class StartPaymentResponse(APIModel):
    data: StartPaymentData


class TransferClaim(APIModel):
    reference: str = Field(min_length=6, max_length=100, pattern=r"^[A-Za-z0-9@._/+:-]+$")


class TransferReview(APIModel):
    decision: Literal["approve", "reject"]
    verified_reference: str = Field(min_length=6, max_length=100, pattern=r"^[A-Za-z0-9@._/+:-]+$")
    note: str = Field(min_length=5, max_length=250)
