"""DTOs for listing managed restaurants."""

from app.ordering.shared.dto import RestaurantView
from app.shared.dto import APIModel


class ManagedRestaurantsData(APIModel):
    restaurants: list[RestaurantView]


class ManagedRestaurantsResponse(APIModel):
    data: ManagedRestaurantsData
