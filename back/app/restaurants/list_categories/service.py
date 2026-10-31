"""Read catalog data without HTTP or SQL dependencies."""

from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import CatalogRepository
from app.restaurants.list_categories.dto import ListCategoriesData, ListCategoriesResponse


class ListCategoriesService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    def execute(self, restaurant_id: str) -> ListCategoriesResponse:
        require_restaurant(self.catalog, restaurant_id)
        return ListCategoriesResponse(
            data=ListCategoriesData(categories=self.catalog.list_categories(restaurant_id))
        )
