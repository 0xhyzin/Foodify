"""Assign an active order preparer to prepare an accepted order."""

from app.infrastructure.models import User
from app.notifications.interfaces import NotificationDispatcherInterface
from app.ordering.models import OrderEvent
from app.ordering.shared.guards import assert_can_manage_restaurant
from app.ordering.shared.interfaces import OrderRepository, RestaurantStaffRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData, GetOrderResponse
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository

from .dto import AssignPreparerRequest

PREPARER_ASSIGNABLE_STATUSES = frozenset({"accepted", "preparing"})


class AssignPreparerService:
    def __init__(
        self,
        orders: OrderRepository,
        users: UserRepository,
        staff: RestaurantStaffRepository,
        notifications: NotificationDispatcherInterface,
        uow: UnitOfWork,
    ) -> None:
        self.orders, self.users, self.staff, self.notifications, self.uow = (
            orders,
            users,
            staff,
            notifications,
            uow,
        )

    def execute(
        self, actor: User, order_id: str, payload: AssignPreparerRequest
    ) -> GetOrderResponse:
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
        if order.status not in PREPARER_ASSIGNABLE_STATUSES:
            raise AppError(
                "invalid_order_state",
                "Order must be accepted or preparing before assigning a preparer.",
                409,
            )

        preparer = self.users.get_by_id(str(payload.preparer_id))
        if preparer is None:
            raise AppError("preparer_not_found", "Order preparer not found.", 404)
        if not preparer.is_active or not any(
            role.code == "order_preparer" for role in preparer.roles
        ):
            raise AppError(
                "invalid_preparer",
                "Selected user is not an active order preparer.",
                400,
            )

        order.assigned_preparer_id = preparer.id
        order.assigned_preparer = preparer
        order.events.append(
            OrderEvent(
                status=order.status,
                actor_id=actor.id,
                note=f"Assigned preparer: {preparer.name}",
                created_at=utcnow(),
            )
        )
        self.uow.flush()
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()

        restaurant_name = order.restaurant.name if order.restaurant else ""
        self.notifications.dispatch(
            event_type="order_assigned_to_preparer",
            order_id=order.id,
            recipient_id=preparer.id,
            details={"restaurant_name": restaurant_name},
        )
        return response
