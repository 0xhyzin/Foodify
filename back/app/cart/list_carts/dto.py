from app.ordering.shared.dto import CartView, Pagination
from app.shared.dto import APIModel


class CartListData(APIModel):
    carts: list[CartView]
    pagination: Pagination


class CartListResponse(APIModel):
    data: CartListData
