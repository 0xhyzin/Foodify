from app.checkout.submit_order.dependencies import Transaction, Users
from app.ordering.shared.dependencies import Carts, Orders
from app.payments.shared.dependencies import HostedGateway

from .interfaces import ProcessCallbackServiceInterface
from .service import ProcessCallbackService


def get_service(
    users: Users, orders: Orders, carts: Carts, gateway: HostedGateway, uow: Transaction
) -> ProcessCallbackServiceInterface:
    return ProcessCallbackService(users, orders, carts, gateway, uow)
