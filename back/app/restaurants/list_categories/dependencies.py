"""Inject the request-scoped catalog adapter."""

from app.ordering.shared.dependencies import Catalog
from app.restaurants.list_categories.interfaces import ListCategoriesServiceInterface
from app.restaurants.list_categories.service import ListCategoriesService


def get_service(catalog: Catalog) -> ListCategoriesServiceInterface:
    return ListCategoriesService(catalog)
