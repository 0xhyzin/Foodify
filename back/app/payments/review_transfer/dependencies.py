from app.checkout.submit_order.dependencies import Transaction, Users
from app.ordering.shared.dependencies import Carts, Orders

from .interfaces import ReviewTransferServiceInterface
from .service import ReviewTransferService


def get_service(
    users: Users, orders: Orders, carts: Carts, uow: Transaction
) -> ReviewTransferServiceInterface:
    return ReviewTransferService(users, orders, carts, uow)
