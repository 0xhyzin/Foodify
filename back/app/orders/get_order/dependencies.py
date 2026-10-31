"""Inject order read adapters."""

from app.ordering.shared.dependencies import Orders
from app.orders.get_order.interfaces import GetOrderServiceInterface
from app.orders.get_order.service import GetOrderService


def get_service(orders: Orders) -> GetOrderServiceInterface:
    return GetOrderService(orders)
