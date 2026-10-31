"""Customer order endpoint restricted to the authenticated account."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.orders.list_orders.dependencies import get_service
from app.orders.list_orders.dto import OrderListQuery, OrderListResponse
from app.orders.list_orders.interfaces import ListOrdersServiceInterface

router = APIRouter(tags=["Customer orders"])
Customer = Annotated[User, Depends(require_permission("orders:read_own"))]
Service = Annotated[ListOrdersServiceInterface, Depends(get_service)]


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    current_user: Customer,
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> OrderListResponse:
    return service.execute(current_user.id, OrderListQuery(limit=limit, offset=offset))
