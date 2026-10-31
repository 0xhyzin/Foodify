"""Order reads keep ownership and bounded pagination explicit."""

from app.ordering.shared.interfaces import OrderRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData, GetOrderResponse
from app.shared.errors import AppError


class GetOrderService:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders

    def execute(self, user_id: str, order_id: str) -> GetOrderResponse:
        order = self.orders.get_owned(order_id, user_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)
        return GetOrderResponse(data=GetOrderData(order=order_view(order)))
