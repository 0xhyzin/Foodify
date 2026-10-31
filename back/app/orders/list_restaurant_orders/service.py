"""Order reads keep ownership and bounded pagination explicit."""

from app.ordering.shared.dto import Pagination
from app.ordering.shared.interfaces import CatalogRepository, OrderRepository
from app.ordering.shared.mappers import order_view
from app.orders.list_restaurant_orders.dto import OrderListData, OrderListQuery, OrderListResponse
from app.shared.errors import AppError


class ListRestaurantOrdersService:
    def __init__(self, orders: OrderRepository, catalog: CatalogRepository) -> None:
        self.orders, self.catalog = orders, catalog

    def execute(self, restaurant_id: str, query: OrderListQuery) -> OrderListResponse:
        if self.catalog.get_restaurant(restaurant_id) is None:
            raise AppError("restaurant_not_found", "Restaurant not found.", 404)
        values = self.orders.list_for_restaurant(restaurant_id, query.limit + 1, query.offset)
        return OrderListResponse(
            data=OrderListData(
                orders=[order_view(value) for value in values[: query.limit]],
                pagination=Pagination(
                    limit=query.limit, offset=query.offset, has_more=len(values) > query.limit
                ),
            )
        )
