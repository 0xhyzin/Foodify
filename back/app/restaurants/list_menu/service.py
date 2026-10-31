"""Read catalog data without HTTP or SQL dependencies."""

from app.ordering.shared.dto import Pagination
from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CatalogRepository
from app.ordering.shared.mappers import menu_view
from app.restaurants.list_menu.dto import ListMenuData, ListMenuQuery, ListMenuResponse


class ListMenuService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    def execute(self, restaurant_id: str, query: ListMenuQuery) -> ListMenuResponse:
        require_restaurant(self.catalog, restaurant_id)
        values = self.catalog.list_menu(
            restaurant_id, query.category, query.limit + 1, query.offset
        )
        return ListMenuResponse(
            data=ListMenuData(
                menu=[menu_view(value) for value in values[: query.limit]],
                pagination=Pagination(
                    limit=query.limit, offset=query.offset, has_more=len(values) > query.limit
                ),
            )
        )
