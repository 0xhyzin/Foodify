"""Order cancellation endpoint for customer owner or authorized restaurant manager."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends

from app.dependencies import get_current_user
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import CancelOrderRequest, GetOrderResponse
from .interfaces import CancelOrderServiceInterface

router = APIRouter(tags=["Customer orders"])


@router.post("/orders/{order_id}/cancel", response_model=GetOrderResponse)
def cancel_order(
    order_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    service: Annotated[CancelOrderServiceInterface, Depends(get_service)],
    payload: Annotated[CancelOrderRequest | None, Body()] = None,
) -> GetOrderResponse:
    return service.execute(actor, str(order_id), payload or CancelOrderRequest())
