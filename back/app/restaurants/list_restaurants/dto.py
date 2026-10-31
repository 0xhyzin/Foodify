"""ListRestaurants input/output contract."""

from typing import Literal

from pydantic import Field

from app.ordering.shared.dto import Pagination, RestaurantView
from app.shared.dto import APIModel


class ListRestaurantsQuery(APIModel):
    category: str | None = Field(default=None, max_length=80)
    search: str | None = Field(default=None, max_length=100)
    kind: Literal["restaurant", "dessert", "grocery"] | None = None
    sort: Literal["rating", "fastest", "delivery_fee"] = "rating"
    free_delivery: bool = False
    max_delivery_minutes: int | None = Field(default=None, ge=1, le=180)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=1000000)


class ListRestaurantsData(APIModel):
    restaurants: list[RestaurantView]
    pagination: Pagination


class ListRestaurantsResponse(APIModel):
    data: ListRestaurantsData
