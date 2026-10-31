"""Inject the request-scoped catalog adapter."""

from app.ordering.shared.dependencies import Catalog
from app.restaurants.list_restaurants.interfaces import ListRestaurantsServiceInterface
from app.restaurants.list_restaurants.service import ListRestaurantsService


def get_service(catalog: Catalog) -> ListRestaurantsServiceInterface:
    return ListRestaurantsService(catalog)
