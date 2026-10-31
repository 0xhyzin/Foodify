"""Application service contract."""

from typing import Protocol

from app.restaurants.get_restaurant.dto import GetRestaurantResponse


class GetRestaurantServiceInterface(Protocol):
    def execute(self, restaurant_id: str) -> GetRestaurantResponse: ...
