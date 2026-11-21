"""Replace the currently assigned courier when permitted."""

from datetime import UTC

from app.delivery.shared import ASSIGNABLE_ORDER_STATUSES, require_active_courier
from app.infrastructure.models import User
from app.notifications.interfaces import NotificationDispatcherInterface
from app.ordering.models import OrderEvent
from app.ordering.shared.guards import assert_can_manage_restaurant
from app.ordering.shared.interfaces import OrderRepository, RestaurantStaffRepository
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository

from .dto import ReassignDeliveryData, ReassignDeliveryRequest, ReassignDeliveryResponse


class ReassignDeliveryService:
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
        self, actor: User, order_id: str, payload: ReassignDeliveryRequest
    ) -> ReassignDeliveryResponse:
        order = self.orders.get_locked(order_id)
        if order is None:
            raise AppError("order_not_found", "Order not found.", 404)
        assert_can_manage_restaurant(actor, order.restaurant_id, self.staff)
        assignment = order.delivery_assignment
        if assignment is None:
            raise AppError(
                "delivery_not_assigned",
                "Order does not have an existing delivery assignment.",
                409,
            )
        if order.status not in ASSIGNABLE_ORDER_STATUSES:
            raise AppError(
                "reassignment_not_allowed",
                "Delivery person cannot be reassigned after pickup or completion.",
                409,
            )
        new_courier = require_active_courier(self.users, str(payload.new_delivery_person_id))
        previous_id = assignment.delivery_person_id
        if new_courier.id == previous_id:
            raise AppError(
                "same_delivery_person",
                "Order is already assigned to this delivery person.",
                409,
            )

        now = utcnow()
        assignment.previous_delivery_person_id = previous_id
        assignment.delivery_person_id = new_courier.id
        assignment.delivery_person = new_courier
        assignment.assigned_by_id = actor.id
        assignment.status = "reassigned"
        assignment.updated_at = now
        order.events.append(
            OrderEvent(
                status=order.status,
                actor_id=actor.id,
                note=f"Reassigned courier: {new_courier.name}",
                created_at=now,
            )
        )
        self.uow.flush()
        response = ReassignDeliveryResponse(
            data=ReassignDeliveryData(
                order_id=order.id,
                previous_delivery_person_id=previous_id,
                new_delivery_person_id=new_courier.id,
                new_delivery_person_name=new_courier.name,
                assignment_status="REASSIGNED",
                updated_at=assignment.updated_at.replace(tzinfo=UTC),
            )
        )
        self.uow.commit()

        restaurant_name = order.restaurant.name if order.restaurant else ""
        self.notifications.dispatch(
            event_type="delivery_reassigned",
            order_id=order.id,
            recipient_id=new_courier.id,
            details={"restaurant_name": restaurant_name},
        )
        return response
