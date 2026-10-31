"""Authenticated cart endpoint with explicit permission and response model."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.cart.remove_item.dependencies import get_service
from app.cart.remove_item.dto import CartResponse
from app.cart.remove_item.interfaces import RemoveCartItemServiceInterface
from app.dependencies import require_permission
from app.infrastructure.models import User

router = APIRouter(tags=["Customer cart"])
Customer = Annotated[User, Depends(require_permission("orders:create"))]
Service = Annotated[RemoveCartItemServiceInterface, Depends(get_service)]


@router.delete("/carts/{restaurant_id}/items/{cart_item_id}", response_model=CartResponse)
def remove_item(
    current_user: Customer, service: Service, restaurant_id: UUID, cart_item_id: UUID
) -> CartResponse:
    return service.execute(current_user.id, str(restaurant_id), str(cart_item_id))
