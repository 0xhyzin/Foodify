"""Order query and public response contract."""

from pydantic import Field

from app.ordering.shared.dto import OrderListData, OrderListResponse
from app.shared.dto import APIModel


class OrderListQuery(APIModel):
    status: str | None = Field(default=None, max_length=30)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=1000000)


__all__ = ["OrderListData", "OrderListResponse"]
