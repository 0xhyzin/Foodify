from app.checkout.submit_order.dependencies import Transaction, Users
from app.ordering.shared.dependencies import Catalog

from .interfaces import SetFavoriteServiceInterface
from .service import SetFavoriteService


def get_service(catalog: Catalog, users: Users, uow: Transaction) -> SetFavoriteServiceInterface:
    return SetFavoriteService(catalog, users, uow)
