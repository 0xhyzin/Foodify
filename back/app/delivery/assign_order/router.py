"""Endpoint for assigning a courier to an order."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import AssignDeliveryRequest, AssignDeliveryResponse
from .interfaces import AssignDeliveryServiceInterface

router = APIRouter(tags=["Delivery"])


@router.post(
    "/orders/{order_id}/delivery-assignment",
    response_model=AssignDeliveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_delivery_person(
    order_id: UUID,
    payload: AssignDeliveryRequest,
    actor: Annotated[User, Depends(require_permission("deliveries:assign"))],
    service: Annotated[AssignDeliveryServiceInterface, Depends(get_service)],
) -> AssignDeliveryResponse:
    return service.execute(actor, str(order_id), payload)
