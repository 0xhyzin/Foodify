from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CatalogRepository
from app.restaurants.shared.dto import FavoritesData, FavoritesResponse
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import UserRepository

from .dto import FavoriteRequest


class SetFavoriteService:
    def __init__(self, catalog: CatalogRepository, users: UserRepository, uow: UnitOfWork) -> None:
        self.catalog = catalog
        self.users, self.uow = users, uow

    def execute(
        self, user_id: str, restaurant_id: str, payload: FavoriteRequest
    ) -> FavoritesResponse:
        require_active_user(self.users, user_id, for_update=True)
        require_restaurant(self.catalog, restaurant_id)
        favorites = self.catalog.list_favorites(user_id, for_update=True)
        if payload.favorite and restaurant_id not in favorites and len(favorites) >= 200:
            raise AppError("favorites_limit", "You can save up to 200 favorites.", 409)
        self.catalog.set_favorite(user_id, restaurant_id, payload.favorite)
        self.uow.flush()
        response = FavoritesResponse(
            data=FavoritesData(restaurant_ids=self.catalog.list_favorites(user_id, for_update=True))
        )
        self.uow.commit()
        return response
