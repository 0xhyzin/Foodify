"""Kitchen / order preparer queue and readiness confirmation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.ordering.shared.dependencies import Orders, Staff
from app.ordering.shared.dto import OrderListData, OrderListResponse, Pagination
from app.ordering.shared.guards import is_global_operator
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderResponse

from .dependencies import get_service
from .dto import KitchenOrderStatusRequest
from .interfaces import KitchenUpdateStatusServiceInterface

router = APIRouter(tags=["Kitchen orders"])
Preparer = Annotated[User, Depends(require_permission("orders:prepare"))]


@router.get("/kitchen/orders", response_model=OrderListResponse)
def list_kitchen_orders(
    current_user: Preparer,
    orders: Orders,
    staff: Staff,
    status: Annotated[str | None, Query(max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> OrderListResponse:
    restaurant_ids = (
        None
        if is_global_operator(current_user)
        else [item.id for item in staff.list_managed_restaurants(current_user.id)]
    )
    items = orders.list_for_preparer(
        current_user.id, restaurant_ids, limit + 1, offset, status=status
    )
    return OrderListResponse(
        data=OrderListData(
            orders=[order_view(item) for item in items[:limit]],
            pagination=Pagination(limit=limit, offset=offset, has_more=len(items) > limit),
        )
    )


@router.patch("/kitchen/orders/{order_id}/status", response_model=GetOrderResponse)
def update_kitchen_order_status(
    order_id: UUID,
    payload: KitchenOrderStatusRequest,
    actor: Preparer,
    service: Annotated[KitchenUpdateStatusServiceInterface, Depends(get_service)],
) -> GetOrderResponse:
    return service.execute(actor, str(order_id), payload)
