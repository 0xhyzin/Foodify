from app.ordering.shared.cart_state import present_cart
from app.ordering.shared.dto import Pagination
from app.ordering.shared.interfaces import CartRepository, CatalogRepository

from .dto import CartListData, CartListResponse


class ListCartsService:
    def __init__(self, carts: CartRepository, catalog: CatalogRepository) -> None:
        self.carts, self.catalog = carts, catalog

    def execute(self, user_id: str, limit: int = 100, offset: int = 0) -> CartListResponse:
        carts = self.carts.list_for_user(user_id, limit + 1, offset)
        return CartListResponse(
            data=CartListData(
                carts=[present_cart(self.catalog, cart).data.cart for cart in carts[:limit]],
                pagination=Pagination(limit=limit, offset=offset, has_more=len(carts) > limit),
            )
        )
