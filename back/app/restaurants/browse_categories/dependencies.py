from app.ordering.shared.dependencies import Catalog

from .interfaces import BrowseCategoriesServiceInterface
from .service import BrowseCategoriesService


def get_service(catalog: Catalog) -> BrowseCategoriesServiceInterface:
    return BrowseCategoriesService(catalog)
