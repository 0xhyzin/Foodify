from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import GetOrderResponse, TransferReview
from .interfaces import ReviewTransferServiceInterface

router = APIRouter(tags=["Payments"])


@router.post("/operations/orders/{order_id}/transfer-review", response_model=GetOrderResponse)
def review_transfer(
    order_id: UUID,
    user: Annotated[User, Depends(require_permission("payments:review"))],
    service: Annotated[ReviewTransferServiceInterface, Depends(get_service)],
    payload: TransferReview,
) -> GetOrderResponse:
    return service.execute(user.id, str(order_id), payload)
