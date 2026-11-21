"""Allow customer or authorized manager to cancel an unaccepted order."""

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

from .dto import CancelOrderRequest, GetOrderResponse

CANCELLABLE_STATUSES = {"awaiting_payment", "pending"}


class CancelOrderService:
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
        self, actor: User, order_id: str, payload: CancelOrderRequest
    ) -> GetOrderResponse:
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)

        is_owner = order.user_id == actor.id
        can_manage = any(
            item.code == "orders:manage"
            for role in actor.roles
            for item in role.permissions
        )
        if not is_owner:
            if can_manage:
                assert_can_manage_restaurant(actor, order.restaurant_id, self.staff)
            else:
                raise AppError(
                    "permission_denied", "You do not have permission to cancel this order.", 403
                )

        if order.status not in CANCELLABLE_STATUSES:
            raise AppError(
                "order_cannot_be_cancelled",
                "Order can only be cancelled before it is accepted.",
                409,
            )

        note = payload.note.strip() if payload.note else None
        order.status = "cancelled"
        order.events.append(
            OrderEvent(
                status="cancelled",
                actor_id=actor.id,
                note=note or "Order cancelled.",
                created_at=utcnow(),
            )
        )
        self.uow.flush()
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()

        restaurant_name = order.restaurant.name if order.restaurant else ""
        self.notifications.dispatch(
            event_type="order_cancelled",
            order_id=order.id,
            recipient_id=order.user_id,
            details={"note": note or "", "restaurant_name": restaurant_name},
        )
        return response
