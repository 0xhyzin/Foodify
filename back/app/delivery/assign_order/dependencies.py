"""Inject delivery assignment service."""

from app.checkout.submit_order.dependencies import Transaction, Users
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders, Staff

from .interfaces import AssignDeliveryServiceInterface
from .service import AssignDeliveryService


def get_service(
    orders: Orders,
    users: Users,
    staff: Staff,
    notifications: Notifications,
    uow: Transaction,
) -> AssignDeliveryServiceInterface:
    return AssignDeliveryService(orders, users, staff, notifications, uow)
