from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import GetOrderResponse, UpdateOrderStatusRequest
from .interfaces import UpdateOrderStatusServiceInterface

router = APIRouter(tags=["Operations orders"])


@router.patch("/operations/orders/{order_id}/status", response_model=GetOrderResponse)
def update_order_status(
    order_id: UUID,
    payload: UpdateOrderStatusRequest,
    actor: Annotated[User, Depends(require_permission("orders:manage"))],
    service: Annotated[UpdateOrderStatusServiceInterface, Depends(get_service)],
) -> GetOrderResponse:
    return service.execute(actor.id, str(order_id), payload)
