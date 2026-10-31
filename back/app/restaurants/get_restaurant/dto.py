"""GetRestaurant input/output contract."""

from app.ordering.shared.dto import RestaurantDetail
from app.shared.dto import APIModel


class GetRestaurantData(APIModel):
    restaurant: RestaurantDetail


class GetRestaurantResponse(APIModel):
    data: GetRestaurantData
