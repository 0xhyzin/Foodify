from app.checkout.submit_order.dependencies import Transaction
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Orders, Staff

from .interfaces import UpdateOrderStatusServiceInterface
from .service import UpdateOrderStatusService


def get_service(
    orders: Orders, staff: Staff, notifications: Notifications, uow: Transaction
) -> UpdateOrderStatusServiceInterface:
    return UpdateOrderStatusService(orders, staff, notifications, uow)
