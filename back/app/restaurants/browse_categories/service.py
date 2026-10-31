from app.ordering.shared.interfaces import CatalogRepository

from .dto import CategoryData, CategoryResponse, CategoryView


class BrowseCategoriesService:
    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    def execute(self) -> CategoryResponse:
        return CategoryResponse(
            data=CategoryData(
                categories=[
                    CategoryView(code=c.code, name=c.name, artwork=c.artwork)
                    for c in self.catalog.list_browse_categories()
                ]
            )
        )
