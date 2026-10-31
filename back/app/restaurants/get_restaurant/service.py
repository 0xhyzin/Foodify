"""Read catalog data without HTTP or SQL dependencies."""

from app.ordering.shared.dto import RestaurantDetail
from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CatalogRepository
from app.ordering.shared.mappers import restaurant_view
from app.restaurants.get_restaurant.dto import GetRestaurantData, GetRestaurantResponse


class GetRestaurantService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    def execute(self, restaurant_id: str) -> GetRestaurantResponse:
        value = require_restaurant(self.catalog, restaurant_id)
        view = RestaurantDetail(
            **restaurant_view(value).model_dump(),
            categories=self.catalog.list_categories(restaurant_id),
        )
        return GetRestaurantResponse(data=GetRestaurantData(restaurant=view))
