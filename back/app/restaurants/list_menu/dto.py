"""ListMenu input/output contract."""

from pydantic import Field

from app.ordering.shared.dto import MenuItemView, Pagination
from app.shared.dto import APIModel


class ListMenuQuery(APIModel):
    category: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=1000000)


class ListMenuData(APIModel):
    menu: list[MenuItemView]
    pagination: Pagination


class ListMenuResponse(APIModel):
    data: ListMenuData
