"""Record courier pickup and delivery completion for assigned orders."""

from app.delivery.shared import require_confirmed_payment
from app.infrastructure.models import User
from app.notifications.interfaces import NotificationDispatcherInterface
from app.ordering.models import OrderEvent
from app.ordering.shared.interfaces import OrderRepository
from app.ordering.shared.mappers import order_view
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow

from .dto import (
    UpdateDeliveryStatusData,
    UpdateDeliveryStatusRequest,
    UpdateDeliveryStatusResponse,
)

DELIVERY_TRANSITIONS: dict[str, str] = {
    "ready_for_pickup": "picked_up",
    "picked_up": "delivered",
}

NOTIFICATION_EVENTS: dict[str, str] = {
    "picked_up": "order_picked_up",
    "delivered": "order_delivered",
}


class UpdateDeliveryStatusService:
    def __init__(
        self,
        orders: OrderRepository,
        notifications: NotificationDispatcherInterface,
        uow: UnitOfWork,
    ) -> None:
        self.orders, self.notifications, self.uow = orders, notifications, uow

    def execute(
        self, actor: User, order_id: str, payload: UpdateDeliveryStatusRequest
    ) -> UpdateDeliveryStatusResponse:
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)
        assignment = order.delivery_assignment
        if assignment is None or assignment.delivery_person_id != actor.id:
            raise AppError(
                "permission_denied", "You can only update orders assigned to you.", 403
            )
        require_confirmed_payment(order)

        previous_status = order.status
        if DELIVERY_TRANSITIONS.get(previous_status) != payload.status:
            raise AppError(
                "invalid_order_transition",
                "Order status must follow the approved delivery sequence.",
                409,
            )

        note = payload.note.strip() if payload.note else None
        order.status = payload.status
        order.events.append(
            OrderEvent(
                status=payload.status,
                actor_id=actor.id,
                note=note,
                created_at=utcnow(),
            )
        )
        if payload.status == "delivered" and order.payment.provider == "cash":
            order.payment.status = "paid"

        self.uow.flush()
        response = UpdateDeliveryStatusResponse(
            data=UpdateDeliveryStatusData(
                order_id=order.id,
                previous_status=previous_status,
                current_status=order.status,
                order=order_view(order),
            )
        )
        self.uow.commit()

        restaurant_name = order.restaurant.name if order.restaurant else ""
        self.notifications.dispatch(
            event_type=NOTIFICATION_EVENTS[payload.status],
            order_id=order.id,
            recipient_id=order.user_id,
            details={"note": note or "", "restaurant_name": restaurant_name},
        )
        return response
