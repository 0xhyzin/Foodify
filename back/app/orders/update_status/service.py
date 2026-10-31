from app.ordering.models import OrderEvent
from app.ordering.shared.interfaces import OrderRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow

from .dto import GetOrderResponse, UpdateOrderStatusRequest

TRANSITIONS = {
    "placed": "preparing",
    "preparing": "ready",
    "ready": "out_for_delivery",
    "out_for_delivery": "delivered",
}


class UpdateOrderStatusService:
    def __init__(self, orders: OrderRepository, uow: UnitOfWork) -> None:
        self.orders, self.uow = orders, uow

    def execute(
        self, actor_id: str, order_id: str, payload: UpdateOrderStatusRequest
    ) -> GetOrderResponse:
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)
        if not order.payment or order.payment.status not in {
            "paid",
            "due_on_delivery",
            "simulated",
        }:
            raise AppError(
                "payment_not_confirmed", "Payment must be verified before fulfillment.", 409
            )
        if order.status != payload.status:
            if TRANSITIONS.get(order.status) != payload.status:
                raise AppError(
                    "invalid_order_transition",
                    "Order status must follow the fulfillment sequence.",
                    409,
                )
            order.status = payload.status
            order.events.append(
                OrderEvent(
                    status=payload.status, actor_id=actor_id, note=payload.note, created_at=utcnow()
                )
            )
            if payload.status == "delivered" and order.payment.provider == "cash":
                order.payment.status = "paid"
        self.uow.flush()
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()
        return response
