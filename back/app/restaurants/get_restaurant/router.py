"""Public catalog endpoint; business logic lives in its service."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.restaurants.get_restaurant.dependencies import get_service
from app.restaurants.get_restaurant.dto import GetRestaurantResponse
from app.restaurants.get_restaurant.interfaces import GetRestaurantServiceInterface

router = APIRouter(tags=["Restaurants"])
Service = Annotated[GetRestaurantServiceInterface, Depends(get_service)]


@router.get("/restaurants/{restaurant_id}", response_model=GetRestaurantResponse)
def get_restaurant(service: Service, restaurant_id: UUID) -> GetRestaurantResponse:
    return service.execute(str(restaurant_id))
