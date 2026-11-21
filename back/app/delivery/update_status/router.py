"""Courier pickup and delivery completion endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import UpdateDeliveryStatusRequest, UpdateDeliveryStatusResponse
from .interfaces import UpdateDeliveryStatusServiceInterface

router = APIRouter(tags=["Delivery"])


@router.patch("/delivery/orders/{order_id}/status", response_model=UpdateDeliveryStatusResponse)
def update_delivery_status(
    order_id: UUID,
    payload: UpdateDeliveryStatusRequest,
    actor: Annotated[User, Depends(require_permission("deliveries:update_assigned"))],
    service: Annotated[UpdateDeliveryStatusServiceInterface, Depends(get_service)],
) -> UpdateDeliveryStatusResponse:
    return service.execute(actor, str(order_id), payload)
