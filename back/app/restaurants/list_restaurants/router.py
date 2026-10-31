"""Public catalog endpoint; business logic lives in its service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.restaurants.list_restaurants.dependencies import get_service
from app.restaurants.list_restaurants.dto import ListRestaurantsQuery, ListRestaurantsResponse
from app.restaurants.list_restaurants.interfaces import ListRestaurantsServiceInterface

router = APIRouter(tags=["Restaurants"])
Service = Annotated[ListRestaurantsServiceInterface, Depends(get_service)]


@router.get("/restaurants", response_model=ListRestaurantsResponse)
def list_restaurants(
    service: Service, query: Annotated[ListRestaurantsQuery, Query()]
) -> ListRestaurantsResponse:
    return service.execute(query)
