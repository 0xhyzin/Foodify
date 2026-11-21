"""Kitchen status transitions and readiness notifications."""

from app.infrastructure.models import User
from app.notifications.interfaces import NotificationDispatcherInterface
from app.ordering.models import OrderEvent
from app.ordering.shared.guards import is_global_operator
from app.ordering.shared.interfaces import OrderRepository, RestaurantStaffRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData, GetOrderResponse
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow

from .dto import KitchenOrderStatusRequest

KITCHEN_TRANSITIONS: dict[str, str] = {
    "accepted": "preparing",
    "preparing": "ready_for_pickup",
}


class KitchenUpdateStatusService:
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
        self, actor: User, order_id: str, payload: KitchenOrderStatusRequest
    ) -> GetOrderResponse:
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)

        if not is_global_operator(actor):
            is_assigned_preparer = order.assigned_preparer_id == actor.id
            is_unassigned_restaurant_staff = (
                order.assigned_preparer_id is None
                and self.staff.is_assigned(order.restaurant_id, actor.id)
            )
            if not (is_assigned_preparer or is_unassigned_restaurant_staff):
                raise AppError(
                    "permission_denied",
                    "You do not have permission to prepare this order.",
                    403,
                )

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

        if KITCHEN_TRANSITIONS.get(order.status) != payload.status:
            raise AppError(
                "invalid_order_transition",
                "Order status must follow the approved preparation sequence.",
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
        self.uow.flush()
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()

        restaurant_name = order.restaurant.name if order.restaurant else ""
        details = {"note": note or "", "restaurant_name": restaurant_name}
        if payload.status == "preparing":
            self.notifications.dispatch(
                event_type="order_preparing",
                order_id=order.id,
                recipient_id=order.user_id,
                details=details,
            )
        elif payload.status == "ready_for_pickup":
            self.notifications.dispatch(
                event_type="order_ready_for_pickup",
                order_id=order.id,
                recipient_id=order.user_id,
                details=details,
            )
            if order.delivery_assignment is not None:
                self.notifications.dispatch(
                    event_type="order_ready_for_courier_pickup",
                    order_id=order.id,
                    recipient_id=order.delivery_assignment.delivery_person_id,
                    details=details,
                )
        return response
