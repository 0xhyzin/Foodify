"""Request/response contracts for delivery reassignment."""

from datetime import datetime
from uuid import UUID

from app.shared.dto import APIModel


class ReassignDeliveryRequest(APIModel):
    new_delivery_person_id: UUID


class ReassignDeliveryData(APIModel):
    order_id: str
    previous_delivery_person_id: str
    new_delivery_person_id: str
    new_delivery_person_name: str
    assignment_status: str
    updated_at: datetime


class ReassignDeliveryResponse(APIModel):
    data: ReassignDeliveryData
