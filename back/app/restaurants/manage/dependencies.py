"""Inject restaurant management service."""

from app.checkout.submit_order.dependencies import Transaction, Users
from app.ordering.shared.dependencies import Catalog, Staff

from .interfaces import ManageRestaurantsServiceInterface
from .service import ManageRestaurantsService


def get_service(
    catalog: Catalog, staff: Staff, users: Users, uow: Transaction
) -> ManageRestaurantsServiceInterface:
    return ManageRestaurantsService(catalog, staff, users, uow)
