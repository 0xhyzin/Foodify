from app.checkout.submit_order.dependencies import Transaction, Users
from app.ordering.shared.dependencies import Orders

from .interfaces import ClaimTransferServiceInterface
from .service import ClaimTransferService


def get_service(users: Users, orders: Orders, uow: Transaction) -> ClaimTransferServiceInterface:
    return ClaimTransferService(users, orders, uow)
