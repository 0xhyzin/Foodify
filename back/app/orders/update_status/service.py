from app.infrastructure.models import User
from app.notifications.interfaces import NotificationDispatcherInterface
from app.ordering.models import OrderEvent
from app.ordering.shared.guards import assert_can_manage_restaurant
from app.ordering.shared.interfaces import OrderRepository, RestaurantStaffRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow

from .dto import GetOrderResponse, UpdateOrderStatusRequest

MANAGER_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"accepted", "rejected"},
    "accepted": {"preparing"},
    "preparing": {"ready_for_pickup"},
}

NOTIFICATION_EVENTS: dict[str, str] = {
    "accepted": "order_accepted",
    "rejected": "order_rejected",
    "preparing": "order_preparing",
    "ready_for_pickup": "order_ready_for_pickup",
}


class UpdateOrderStatusService:
    def __init__(
        self,
        orders: OrderRepository,
        staff: RestaurantStaffRepository,
        notifications: NotificationDispatcherInterface,
        uow: UnitOfWork,
    ) -> None:
        self.orders, self.staff, self.notifications, self.uow = (
            orders,
            staff,
            notifications,
            uow,
        )

    def execute(
        self, actor: User, order_id: str, payload: UpdateOrderStatusRequest
    ) -> GetOrderResponse:
        if payload.status in {"picked_up", "delivered"}:
            raise AppError(
                "permission_denied",
                "Only the assigned delivery person can update pickup or delivery status.",
                403,
            )
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)
        assert_can_manage_restaurant(actor, order.restaurant_id, self.staff)
        if not order.payment or order.payment.status not in {
            "paid",
            "due_on_delivery",
            "simulated",
        }:
            raise AppError(
                "payment_not_confirmed", "Payment must be verified before fulfillment.", 409
            )
        if order.status == payload.status:
            self.uow.flush()
            response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
            self.uow.commit()
            return response

        allowed_targets = MANAGER_TRANSITIONS.get(order.status, set())
        if payload.status not in allowed_targets:
            raise AppError(
                "invalid_order_transition",
                "Order status must follow the approved fulfillment sequence.",
                409,
            )
        note = payload.note.strip() if payload.note else None
        event_note = note
        if payload.status == "rejected" and order.payment.status == "paid":
            refund_note = "Paid order rejected; refund review required."
            event_note = f"{note} ({refund_note})" if note else refund_note

        order.status = payload.status
        order.events.append(
            OrderEvent(
                status=payload.status,
                actor_id=actor.id,
                note=event_note,
                created_at=utcnow(),
            )
        )
        self.uow.flush()
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()

        event_type = NOTIFICATION_EVENTS.get(payload.status)
        if event_type:
            restaurant_name = order.restaurant.name if order.restaurant else ""
            details = {"note": note or "", "restaurant_name": restaurant_name}
            self.notifications.dispatch(
                event_type=event_type,
                order_id=order.id,
                recipient_id=order.user_id,
                details=details,
            )
            if payload.status == "accepted":
                for preparer_id in self.staff.list_preparer_user_ids_for_restaurant(
                    order.restaurant_id
                ):
                    self.notifications.dispatch(
                        event_type="order_assigned_to_preparer",
                        order_id=order.id,
                        recipient_id=preparer_id,
                        details=details,
                    )
            elif payload.status == "ready_for_pickup" and order.delivery_assignment is not None:
                self.notifications.dispatch(
                    event_type="order_ready_for_courier_pickup",
                    order_id=order.id,
                    recipient_id=order.delivery_assignment.delivery_person_id,
                    details=details,
                )
        return response
