from typing import Protocol

from app.restaurants.shared.dto import FavoritesResponse


class ListFavoritesServiceInterface(Protocol):
    def execute(self, user_id: str) -> FavoritesResponse: ...
