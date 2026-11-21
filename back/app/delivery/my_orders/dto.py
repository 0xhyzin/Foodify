"""Response contract for courier's assigned orders."""

from app.ordering.shared.dto import OrderView, Pagination
from app.shared.dto import APIModel


class DeliveryOrdersData(APIModel):
    delivery_person_id: str
    orders: list[OrderView]
    pagination: Pagination


class DeliveryOrdersResponse(APIModel):
    data: DeliveryOrdersData
