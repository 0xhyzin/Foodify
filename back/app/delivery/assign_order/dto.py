"""Request/response contracts for delivery assignment."""

from datetime import datetime
from uuid import UUID

from app.shared.dto import APIModel


class AssignDeliveryRequest(APIModel):
    delivery_person_id: UUID


class AssignDeliveryData(APIModel):
    order_id: str
    delivery_person_id: str
    delivery_person_name: str
    assignment_status: str
    assigned_at: datetime


class AssignDeliveryResponse(APIModel):
    data: AssignDeliveryData
