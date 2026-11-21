"""Endpoint for reassigning a delivery courier."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import ReassignDeliveryRequest, ReassignDeliveryResponse
from .interfaces import ReassignDeliveryServiceInterface

router = APIRouter(tags=["Delivery"])


@router.patch("/orders/{order_id}/delivery-assignment", response_model=ReassignDeliveryResponse)
def reassign_delivery_person(
    order_id: UUID,
    payload: ReassignDeliveryRequest,
    actor: Annotated[User, Depends(require_permission("deliveries:assign"))],
    service: Annotated[ReassignDeliveryServiceInterface, Depends(get_service)],
) -> ReassignDeliveryResponse:
    return service.execute(actor, str(order_id), payload)
