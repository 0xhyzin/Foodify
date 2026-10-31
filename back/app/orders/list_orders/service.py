"""Order reads keep ownership and bounded pagination explicit."""

from app.ordering.shared.dto import Pagination
from app.ordering.shared.interfaces import OrderRepository
from app.ordering.shared.mappers import order_view
from app.orders.list_orders.dto import OrderListData, OrderListQuery, OrderListResponse


class ListOrdersService:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders

    def execute(self, user_id: str, query: OrderListQuery) -> OrderListResponse:
        values = self.orders.list_for_user(user_id, query.limit + 1, query.offset)
        return OrderListResponse(
            data=OrderListData(
                orders=[order_view(value) for value in values[: query.limit]],
                pagination=Pagination(
                    limit=query.limit, offset=query.offset, has_more=len(values) > query.limit
                ),
            )
        )
