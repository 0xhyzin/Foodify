"""Application service contract."""

from typing import Protocol

from app.restaurants.list_categories.dto import ListCategoriesResponse


class ListCategoriesServiceInterface(Protocol):
    def execute(self, restaurant_id: str) -> ListCategoriesResponse: ...
