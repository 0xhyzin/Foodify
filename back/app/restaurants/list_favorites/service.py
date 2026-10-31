from app.ordering.shared.interfaces import CatalogRepository
from app.restaurants.shared.dto import FavoritesData, FavoritesResponse


class ListFavoritesService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    def execute(self, user_id: str) -> FavoritesResponse:
        return FavoritesResponse(
            data=FavoritesData(restaurant_ids=self.catalog.list_favorites(user_id))
        )
