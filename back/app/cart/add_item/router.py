"""Authenticated cart endpoint with explicit permission and response model."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.cart.add_item.dependencies import get_service
from app.cart.add_item.dto import AddCartItemRequest, CartResponse
from app.cart.add_item.interfaces import AddCartItemServiceInterface
from app.dependencies import require_permission
from app.infrastructure.models import User

router = APIRouter(tags=["Customer cart"])
Customer = Annotated[User, Depends(require_permission("orders:create"))]
Service = Annotated[AddCartItemServiceInterface, Depends(get_service)]


@router.post("/carts/{restaurant_id}/items", response_model=CartResponse, status_code=201)
def add_item(
    current_user: Customer, service: Service, restaurant_id: UUID, payload: AddCartItemRequest
) -> CartResponse:
    return service.execute(current_user.id, str(restaurant_id), payload)
