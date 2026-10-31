"""Inject order read adapters."""

from app.ordering.shared.dependencies import Orders
from app.orders.list_orders.interfaces import ListOrdersServiceInterface
from app.orders.list_orders.service import ListOrdersService


def get_service(orders: Orders) -> ListOrdersServiceInterface:
    return ListOrdersService(orders)
