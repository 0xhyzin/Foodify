"""Inject order read adapters."""

from app.ordering.shared.dependencies import Catalog, Orders
from app.orders.list_restaurant_orders.interfaces import ListRestaurantOrdersServiceInterface
from app.orders.list_restaurant_orders.service import ListRestaurantOrdersService


def get_service(orders: Orders, catalog: Catalog) -> ListRestaurantOrdersServiceInterface:
    return ListRestaurantOrdersService(orders, catalog)
