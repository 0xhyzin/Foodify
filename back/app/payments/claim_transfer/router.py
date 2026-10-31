from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import GetOrderResponse, TransferClaim
from .interfaces import ClaimTransferServiceInterface

router = APIRouter(tags=["Payments"])


@router.post("/orders/{order_id}/transfer-claim", response_model=GetOrderResponse)
def claim_transfer(
    order_id: UUID,
    user: Annotated[User, Depends(require_permission("orders:read_own"))],
    service: Annotated[ClaimTransferServiceInterface, Depends(get_service)],
    payload: TransferClaim,
) -> GetOrderResponse:
    return service.execute(user.id, str(order_id), payload)
