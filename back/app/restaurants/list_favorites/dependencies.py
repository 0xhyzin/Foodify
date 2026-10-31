from app.ordering.shared.dependencies import Catalog

from .interfaces import ListFavoritesServiceInterface
from .service import ListFavoritesService


def get_service(catalog: Catalog) -> ListFavoritesServiceInterface:
    return ListFavoritesService(catalog)
