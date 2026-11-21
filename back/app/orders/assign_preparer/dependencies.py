"""Inject preparer assignment service."""

from app.checkout.submit_order.dependencies import Transaction, Users
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders, Staff

from .interfaces import AssignPreparerServiceInterface
from .service import AssignPreparerService


def get_service(
    orders: Orders,
    users: Users,
    staff: Staff,
    notifications: Notifications,
    uow: Transaction,
) -> AssignPreparerServiceInterface:
    return AssignPreparerService(orders, users, staff, notifications, uow)
