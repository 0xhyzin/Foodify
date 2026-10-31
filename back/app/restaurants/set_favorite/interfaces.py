from typing import Protocol

from app.restaurants.shared.dto import FavoritesResponse

from .dto import FavoriteRequest


class SetFavoriteServiceInterface(Protocol):
    def execute(
        self, user_id: str, restaurant_id: str, payload: FavoriteRequest
    ) -> FavoritesResponse: ...
