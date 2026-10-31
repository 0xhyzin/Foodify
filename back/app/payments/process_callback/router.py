from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .dependencies import get_service
from .dto import CallbackResponse
from .interfaces import ProcessCallbackServiceInterface

router = APIRouter(tags=["Payments"])


@router.post("/payments/paymob/callback", response_model=CallbackResponse)
def process_callback(
    payload: dict,
    service: Annotated[ProcessCallbackServiceInterface, Depends(get_service)],
    hmac: Annotated[str, Query(min_length=128, max_length=128)],
) -> CallbackResponse:
    service.execute(payload, hmac)
    return CallbackResponse(received=True)
