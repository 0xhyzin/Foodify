"""Create the authenticated user's cart or return their existing cart unchanged."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.cart.create_cart.dependencies import get_service
from app.cart.create_cart.dto import CartResponse
from app.cart.create_cart.interfaces import CreateCartServiceInterface
from app.dependencies import require_permission
from app.infrastructure.models import User

router = APIRouter(tags=["Customer cart"])
Customer = Annotated[User, Depends(require_permission("orders:create"))]
Service = Annotated[CreateCartServiceInterface, Depends(get_service)]


@router.post("/carts/{restaurant_id}", response_model=CartResponse)
def create_or_get_my_cart(
    current_user: Customer, service: Service, restaurant_id: UUID
) -> CartResponse:
    """Returns 200 for both a newly created cart and the already existing cart."""
    return service.execute(current_user.id, str(restaurant_id))
