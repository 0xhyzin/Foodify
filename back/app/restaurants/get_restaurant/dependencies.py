"""Inject the request-scoped catalog adapter."""

from app.ordering.shared.dependencies import Catalog
from app.restaurants.get_restaurant.interfaces import GetRestaurantServiceInterface
from app.restaurants.get_restaurant.service import GetRestaurantService


def get_service(catalog: Catalog) -> GetRestaurantServiceInterface:
    return GetRestaurantService(catalog)
