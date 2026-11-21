"""Inject cancel order service."""

from app.checkout.submit_order.dependencies import Transaction
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders, Staff

from .interfaces import CancelOrderServiceInterface
from .service import CancelOrderService


def get_service(
    orders: Orders, staff: Staff, notifications: Notifications, uow: Transaction
) -> CancelOrderServiceInterface:
    return CancelOrderService(orders, staff, notifications, uow)
