"""Operational restaurant scope listing endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.orders.list_managed_restaurants.dependencies import get_service
from app.orders.list_managed_restaurants.dto import ManagedRestaurantsResponse
from app.orders.list_managed_restaurants.interfaces import ListManagedRestaurantsServiceInterface

router = APIRouter(tags=["Operations orders"])
OrdersReader = Annotated[User, Depends(require_permission("orders:read"))]
Service = Annotated[ListManagedRestaurantsServiceInterface, Depends(get_service)]


@router.get("/operations/restaurants", response_model=ManagedRestaurantsResponse)
def list_managed_restaurants(
    current_user: OrdersReader,
    service: Service,
) -> ManagedRestaurantsResponse:
    return service.execute(current_user)
