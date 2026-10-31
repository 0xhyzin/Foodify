from app.checkout.submit_order.dependencies import Transaction
from app.ordering.shared.dependencies import Orders

from .interfaces import UpdateOrderStatusServiceInterface
from .service import UpdateOrderStatusService


def get_service(orders: Orders, uow: Transaction) -> UpdateOrderStatusServiceInterface:
    return UpdateOrderStatusService(orders, uow)
