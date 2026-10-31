"""Read catalog data without HTTP or SQL dependencies."""

from app.ordering.shared.dto import Pagination
from app.ordering.shared.interfaces import CatalogRepository
from app.ordering.shared.mappers import restaurant_view
from app.restaurants.list_restaurants.dto import (
    ListRestaurantsData,
    ListRestaurantsQuery,
    ListRestaurantsResponse,
)


class ListRestaurantsService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    def execute(self, query: ListRestaurantsQuery) -> ListRestaurantsResponse:
        values = self.catalog.list_restaurants(
            query.category,
            query.search,
            query.limit + 1,
            query.offset,
            query.kind,
            query.sort,
            query.free_delivery,
            query.max_delivery_minutes,
        )
        return ListRestaurantsResponse(
            data=ListRestaurantsData(
                restaurants=[restaurant_view(value) for value in values[: query.limit]],
                pagination=Pagination(
                    limit=query.limit, offset=query.offset, has_more=len(values) > query.limit
                ),
            )
        )
