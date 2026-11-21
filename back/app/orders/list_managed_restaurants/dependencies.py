"""Inject managed restaurants service."""

from app.ordering.shared.dependencies import Staff
from app.orders.list_managed_restaurants.interfaces import ListManagedRestaurantsServiceInterface
from app.orders.list_managed_restaurants.service import ListManagedRestaurantsService


def get_service(staff: Staff) -> ListManagedRestaurantsServiceInterface:
    return ListManagedRestaurantsService(staff)
