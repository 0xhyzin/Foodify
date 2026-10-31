"""Checkout requires authentication, order creation permission, and a retry key."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header

from app.checkout.submit_order.dependencies import get_service
from app.checkout.submit_order.dto import CheckoutRequest, CheckoutResponse
from app.checkout.submit_order.interfaces import CheckoutServiceInterface
from app.dependencies import require_permission
from app.infrastructure.models import User

router = APIRouter(tags=["Checkout"])
Customer = Annotated[User, Depends(require_permission("orders:create"))]
Service = Annotated[CheckoutServiceInterface, Depends(get_service)]
IdempotencyKey = Annotated[
    UUID,
    Header(
        alias="Idempotency-Key",
        description="A fresh UUID per checkout. Retry the same request with the same key.",
    ),
]


@router.post("/checkout", response_model=CheckoutResponse, status_code=201)
def submit_order(
    payload: CheckoutRequest,
    current_user: Customer,
    service: Service,
    idempotency_key: IdempotencyKey,
) -> CheckoutResponse:
    return service.execute(current_user.id, str(idempotency_key), payload)
