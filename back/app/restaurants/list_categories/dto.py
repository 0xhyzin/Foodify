"""ListCategories input/output contract."""

from app.shared.dto import APIModel


class ListCategoriesData(APIModel):
    categories: list[str]


class ListCategoriesResponse(APIModel):
    data: ListCategoriesData
