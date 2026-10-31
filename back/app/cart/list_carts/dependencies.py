from app.ordering.shared.dependencies import Carts, Catalog

from .interfaces import ListCartsServiceInterface
from .service import ListCartsService


def get_service(carts: Carts, catalog: Catalog) -> ListCartsServiceInterface:
    return ListCartsService(carts, catalog)
