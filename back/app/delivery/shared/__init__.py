"""Shared delivery validation helpers."""

from app.infrastructure.models import User
from app.ordering.models import FoodOrder
from app.shared.errors import AppError
from app.users.shared.interfaces import UserRepository

ASSIGNABLE_ORDER_STATUSES = frozenset({"accepted", "preparing", "ready_for_pickup"})


def require_confirmed_payment(order: FoodOrder) -> None:
    if not order.payment or order.payment.status not in {"paid", "due_on_delivery", "simulated"}:
        raise AppError(
            "payment_not_confirmed", "Payment must be verified before fulfillment.", 409
        )


def require_active_courier(users: UserRepository, user_id: str) -> User:
    courier = users.get_by_id(user_id)
    if courier is None:
        raise AppError("delivery_person_not_found", "Delivery person not found.", 404)
    if not courier.is_active or not any(role.code == "courier" for role in courier.roles):
        raise AppError(
            "invalid_delivery_person", "Selected user is not an active delivery courier.", 400
        )
    return courier
