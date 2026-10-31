"""Authenticated cart endpoint with explicit permission and response model."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.cart.clear_cart.dependencies import get_service
from app.cart.clear_cart.dto import CartResponse
from app.cart.clear_cart.interfaces import ClearCartServiceInterface
from app.dependencies import require_permission
from app.infrastructure.models import User

router = APIRouter(tags=["Customer cart"])
Customer = Annotated[User, Depends(require_permission("orders:create"))]
Service = Annotated[ClearCartServiceInterface, Depends(get_service)]


@router.delete("/carts/{restaurant_id}", response_model=CartResponse)
def clear_cart(current_user: Customer, service: Service, restaurant_id: UUID) -> CartResponse:
    return service.execute(current_user.id, str(restaurant_id))
