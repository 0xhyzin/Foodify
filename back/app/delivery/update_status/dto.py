"""Request/response contracts for courier delivery status updates."""

from pydantic import Field, field_validator

from app.ordering.shared.dto import OrderView
from app.shared.dto import APIModel

ALLOWED_DELIVERY_STATUSES = {"picked_up", "delivered"}


class UpdateDeliveryStatusRequest(APIModel):
    status: str
    note: str | None = Field(default=None, max_length=250)

    @field_validator("status")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_DELIVERY_STATUSES:
            raise ValueError("Status must be PICKED_UP or DELIVERED.")
        return normalized


class UpdateDeliveryStatusData(APIModel):
    order_id: str
    previous_status: str
    current_status: str
    order: OrderView


class UpdateDeliveryStatusResponse(APIModel):
    data: UpdateDeliveryStatusData
