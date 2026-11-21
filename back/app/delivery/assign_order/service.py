"""Assign an active courier to an eligible order."""

from datetime import UTC

from app.delivery.shared import (
    ASSIGNABLE_ORDER_STATUSES,
    require_active_courier,
    require_confirmed_payment,
)
from app.infrastructure.models import User
from app.notifications.interfaces import NotificationDispatcherInterface
from app.ordering.models import DeliveryAssignment, OrderEvent
from app.ordering.shared.guards import assert_can_manage_restaurant
from app.ordering.shared.interfaces import OrderRepository, RestaurantStaffRepository
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository

from .dto import AssignDeliveryData, AssignDeliveryRequest, AssignDeliveryResponse


class AssignDeliveryService:
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
        self, actor: User, order_id: str, payload: AssignDeliveryRequest
    ) -> AssignDeliveryResponse:
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)
        assert_can_manage_restaurant(actor, order.restaurant_id, self.staff)
        require_confirmed_payment(order)
        if order.delivery_assignment is not None:
            raise AppError(
                "delivery_already_assigned",
                "This order already has an assigned delivery person.",
                409,
            )
        if order.status not in ASSIGNABLE_ORDER_STATUSES:
            raise AppError(
                "invalid_order_state",
                "Order is not eligible for delivery assignment in its current status.",
                409,
            )
        courier = require_active_courier(self.users, str(payload.delivery_person_id))
        now = utcnow()
        assignment = DeliveryAssignment(
            order_id=order.id,
            delivery_person_id=courier.id,
            assigned_by_id=actor.id,
            status="assigned",
            assigned_at=now,
            updated_at=now,
            delivery_person=courier,
        )
        order.delivery_assignment = assignment
        order.events.append(
            OrderEvent(
                status=order.status,
                actor_id=actor.id,
                note=f"Assigned courier: {courier.name}",
                created_at=now,
            )
        )
        self.uow.flush()
        response = AssignDeliveryResponse(
            data=AssignDeliveryData(
                order_id=order.id,
                delivery_person_id=courier.id,
                delivery_person_name=courier.name,
                assignment_status="ASSIGNED",
                assigned_at=assignment.assigned_at.replace(tzinfo=UTC),
            )
        )
        self.uow.commit()

        restaurant_name = order.restaurant.name if order.restaurant else ""
        self.notifications.dispatch(
            event_type="delivery_assigned",
            order_id=order.id,
            recipient_id=courier.id,
            details={"restaurant_name": restaurant_name},
        )
        return response
