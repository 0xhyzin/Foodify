"""Inject the request-scoped catalog adapter."""

from app.ordering.shared.dependencies import Catalog
from app.restaurants.list_menu.interfaces import ListMenuServiceInterface
from app.restaurants.list_menu.service import ListMenuService


def get_service(catalog: Catalog) -> ListMenuServiceInterface:
    return ListMenuService(catalog)
