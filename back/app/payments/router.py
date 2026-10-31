from uuid import UUID

from fastapi import APIRouter
from starlette.responses import RedirectResponse

from app.core.config import get_settings

from .claim_transfer.router import router as claim
from .list_methods.router import router as methods
from .process_callback.router import router as callback
from .review_transfer.router import router as review
from .start_payment.router import router as start

router = APIRouter()
for operation in (start, callback, claim, review, methods):
    router.include_router(operation)


@router.get("/payments/return/{order_id}", include_in_schema=False)
def return_to_order(order_id: UUID) -> RedirectResponse:
    # Ignore every provider redirect status/query. The authenticated order API is authoritative.
    return RedirectResponse(
        get_settings().frontend_url.rstrip("/") + "/#/orders/" + str(order_id), status_code=303
    )
