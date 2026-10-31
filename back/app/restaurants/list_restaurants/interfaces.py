"""Application service contract."""

from typing import Protocol

from app.restaurants.list_restaurants.dto import ListRestaurantsQuery, ListRestaurantsResponse


class ListRestaurantsServiceInterface(Protocol):
    def execute(self, query: ListRestaurantsQuery) -> ListRestaurantsResponse: ...
