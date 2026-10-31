from app.checkout.submit_order.dependencies import Transaction, Users
from app.ordering.shared.dependencies import Orders
from app.payments.shared.dependencies import HostedGateway

from .interfaces import StartPaymentServiceInterface
from .service import StartPaymentService


def get_service(
    users: Users, orders: Orders, gateway: HostedGateway, uow: Transaction
) -> StartPaymentServiceInterface:
    return StartPaymentService(users, orders, gateway, uow)
