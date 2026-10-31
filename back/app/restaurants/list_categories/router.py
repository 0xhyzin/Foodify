"""Public catalog endpoint; business logic lives in its service."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.restaurants.list_categories.dependencies import get_service
from app.restaurants.list_categories.dto import ListCategoriesResponse
from app.restaurants.list_categories.interfaces import ListCategoriesServiceInterface

router = APIRouter(tags=["Restaurants"])
Service = Annotated[ListCategoriesServiceInterface, Depends(get_service)]


@router.get("/restaurants/{restaurant_id}/categories", response_model=ListCategoriesResponse)
def list_categories(service: Service, restaurant_id: UUID) -> ListCategoriesResponse:
    return service.execute(str(restaurant_id))
