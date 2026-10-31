from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import StartPaymentResponse
from .interfaces import StartPaymentServiceInterface

router = APIRouter(tags=["Payments"])


@router.post("/orders/{order_id}/payment", response_model=StartPaymentResponse)
def start_payment(
    order_id: UUID,
    user: Annotated[User, Depends(require_permission("orders:read_own"))],
    service: Annotated[StartPaymentServiceInterface, Depends(get_service)],
) -> StartPaymentResponse:
    return service.execute(user.id, str(order_id))
