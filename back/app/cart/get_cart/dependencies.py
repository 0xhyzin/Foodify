"""Inject only the two read adapters this operation needs."""

from app.cart.get_cart.interfaces import GetCartServiceInterface
from app.cart.get_cart.service import GetCartService
from app.ordering.shared.dependencies import Carts, Catalog


def get_service(carts: Carts, catalog: Catalog) -> GetCartServiceInterface:
    return GetCartService(carts, catalog)
