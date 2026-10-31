"""Customer order endpoint restricted to the authenticated account."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.orders.get_order.dependencies import get_service
from app.orders.get_order.dto import GetOrderResponse
from app.orders.get_order.interfaces import GetOrderServiceInterface

router = APIRouter(tags=["Customer orders"])
Customer = Annotated[User, Depends(require_permission("orders:read_own"))]
Service = Annotated[GetOrderServiceInterface, Depends(get_service)]


@router.get("/orders/{order_id}", response_model=GetOrderResponse)
def get_order(current_user: Customer, service: Service, order_id: UUID) -> GetOrderResponse:
    return service.execute(current_user.id, str(order_id))
