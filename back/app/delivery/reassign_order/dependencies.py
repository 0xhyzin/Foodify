"""Inject delivery reassignment service."""

from app.checkout.submit_order.dependencies import Transaction, Users
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders, Staff

from .interfaces import ReassignDeliveryServiceInterface
from .service import ReassignDeliveryService


def get_service(
    orders: Orders,
    users: Users,
    staff: Staff,
    notifications: Notifications,
    uow: Transaction,
) -> ReassignDeliveryServiceInterface:
    return ReassignDeliveryService(orders, users, staff, notifications, uow)
