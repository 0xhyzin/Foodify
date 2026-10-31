from app.shared.dto import APIModel


class CategoryView(APIModel):
    code: str
    name: str
    artwork: str


class CategoryData(APIModel):
    categories: list[CategoryView]


class CategoryResponse(APIModel):
    data: CategoryData
