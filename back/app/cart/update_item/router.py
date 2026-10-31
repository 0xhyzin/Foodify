"""Authenticated cart endpoint with explicit permission and response model."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.cart.update_item.dependencies import get_service
from app.cart.update_item.dto import CartResponse, UpdateCartItemRequest
from app.cart.update_item.interfaces import UpdateCartItemServiceInterface
from app.dependencies import require_permission
from app.infrastructure.models import User

router = APIRouter(tags=["Customer cart"])
Customer = Annotated[User, Depends(require_permission("orders:create"))]
Service = Annotated[UpdateCartItemServiceInterface, Depends(get_service)]


@router.patch("/carts/{restaurant_id}/items/{cart_item_id}", response_model=CartResponse)
def update_item(
    current_user: Customer,
    service: Service,
    restaurant_id: UUID,
    cart_item_id: UUID,
    payload: UpdateCartItemRequest,
) -> CartResponse:
    return service.execute(current_user.id, str(restaurant_id), str(cart_item_id), payload)
