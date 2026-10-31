from typing import Annotated

from fastapi import APIRouter, Depends

from .dependencies import get_service
from .dto import PaymentMethodsResponse
from .interfaces import ListMethodsServiceInterface

router = APIRouter(tags=["Payments"])


@router.get("/payments/methods", response_model=PaymentMethodsResponse)
def list_methods(
    service: Annotated[ListMethodsServiceInterface, Depends(get_service)],
) -> PaymentMethodsResponse:
    return service.execute()
