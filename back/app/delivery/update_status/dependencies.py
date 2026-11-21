"""Inject courier delivery status service."""

from app.checkout.submit_order.dependencies import Transaction
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders

from .interfaces import UpdateDeliveryStatusServiceInterface
from .service import UpdateDeliveryStatusService


def get_service(
    orders: Orders, notifications: Notifications, uow: Transaction
) -> UpdateDeliveryStatusServiceInterface:
    return UpdateDeliveryStatusService(orders, notifications, uow)
