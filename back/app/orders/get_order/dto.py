"""Order query and public response contract."""

from app.ordering.shared.dto import OrderView
from app.shared.dto import APIModel


class GetOrderData(APIModel):
    order: OrderView


class GetOrderResponse(APIModel):
    data: GetOrderData
