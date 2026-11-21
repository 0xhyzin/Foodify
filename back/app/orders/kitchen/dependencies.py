"""Inject kitchen preparation service."""

from app.checkout.submit_order.dependencies import Transaction
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders, Staff

from .interfaces import KitchenUpdateStatusServiceInterface
from .service import KitchenUpdateStatusService


def get_service(
    orders: Orders, staff: Staff, notifications: Notifications, uow: Transaction
) -> KitchenUpdateStatusServiceInterface:
    return KitchenUpdateStatusService(orders, staff, notifications, uow)
