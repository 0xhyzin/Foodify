"""Order reads keep ownership and bounded pagination explicit."""

from app.infrastructure.models import User
from app.ordering.shared.dto import Pagination
from app.ordering.shared.guards import assert_can_manage_restaurant
from app.ordering.shared.interfaces import (
    CatalogRepository,
    OrderRepository,
    RestaurantStaffRepository,
)
from app.ordering.shared.mappers import order_view
from app.orders.list_restaurant_orders.dto import OrderListData, OrderListQuery, OrderListResponse
from app.shared.errors import AppError


class ListRestaurantOrdersService:
    def __init__(
        self,
        orders: OrderRepository,
        catalog: CatalogRepository,
        staff: RestaurantStaffRepository,
    ) -> None:
        self.orders, self.catalog, self.staff = orders, catalog, staff

    def execute(
        self, actor: User, restaurant_id: str, query: OrderListQuery
    ) -> OrderListResponse:
        assert_can_manage_restaurant(actor, restaurant_id, self.staff)
        if self.catalog.get_restaurant(restaurant_id) is None:
            raise AppError("restaurant_not_found", "Restaurant not found.", 404)
        values = self.orders.list_for_restaurant(
            restaurant_id, query.limit + 1, query.offset, status=query.status
        )
        return OrderListResponse(
            data=OrderListData(
                orders=[order_view(value) for value in values[: query.limit]],
                pagination=Pagination(
                    limit=query.limit, offset=query.offset, has_more=len(values) > query.limit
                ),
            )
        )
