from app.checkout.submit_order.dependencies import Transaction, Users
from app.notifications.dependencies import Notifications
from app.ordering.shared.dependencies import Carts, Orders

from .interfaces import ReviewTransferServiceInterface
from .service import ReviewTransferService


def get_service(
    users: Users,
    orders: Orders,
    carts: Carts,
    uow: Transaction,
    notifications: Notifications,
) -> ReviewTransferServiceInterface:
    return ReviewTransferService(users, orders, carts, uow, notifications)
