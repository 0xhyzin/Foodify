"""Global operations staff only; no restaurant-owner assignment is claimed."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.orders.list_restaurant_orders.dependencies import get_service
from app.orders.list_restaurant_orders.dto import OrderListQuery, OrderListResponse
from app.orders.list_restaurant_orders.interfaces import ListRestaurantOrdersServiceInterface

router = APIRouter(tags=["Operations orders"])
OperationsStaff = Annotated[User, Depends(require_permission("orders:manage"))]
Service = Annotated[ListRestaurantOrdersServiceInterface, Depends(get_service)]


@router.get("/restaurant/orders", response_model=OrderListResponse)
def list_restaurant_orders(
    current_user: OperationsStaff,
    service: Service,
    restaurant_id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> OrderListResponse:
    return service.execute(str(restaurant_id), OrderListQuery(limit=limit, offset=offset))
