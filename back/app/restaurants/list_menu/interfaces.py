"""Application service contract."""

from typing import Protocol

from app.restaurants.list_menu.dto import ListMenuQuery, ListMenuResponse


class ListMenuServiceInterface(Protocol):
    def execute(self, restaurant_id: str, query: ListMenuQuery) -> ListMenuResponse: ...
