"""Courier's assigned orders endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.ordering.shared.dependencies import Orders
from app.ordering.shared.dto import Pagination
from app.ordering.shared.mappers import order_view

from .dto import DeliveryOrdersData, DeliveryOrdersResponse

router = APIRouter(tags=["Delivery"])


@router.get("/delivery/my-orders", response_model=DeliveryOrdersResponse)
def list_my_delivery_orders(
    current_user: Annotated[User, Depends(require_permission("deliveries:read_assigned"))],
    orders: Orders,
    status: Annotated[str | None, Query(max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> DeliveryOrdersResponse:
    items = orders.list_for_courier(current_user.id, limit + 1, offset, status=status)
    return DeliveryOrdersResponse(
        data=DeliveryOrdersData(
            delivery_person_id=current_user.id,
            orders=[order_view(item) for item in items[:limit]],
            pagination=Pagination(limit=limit, offset=offset, has_more=len(items) > limit),
        )
    )
