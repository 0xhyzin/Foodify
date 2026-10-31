"""Public catalog endpoint; business logic lives in its service."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.restaurants.list_menu.dependencies import get_service
from app.restaurants.list_menu.dto import ListMenuQuery, ListMenuResponse
from app.restaurants.list_menu.interfaces import ListMenuServiceInterface

router = APIRouter(tags=["Restaurants"])
Service = Annotated[ListMenuServiceInterface, Depends(get_service)]


@router.get("/restaurants/{restaurant_id}/menu", response_model=ListMenuResponse)
def list_menu(
    service: Service,
    restaurant_id: UUID,
    category: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> ListMenuResponse:
    return service.execute(
        str(restaurant_id), ListMenuQuery(category=category, limit=limit, offset=offset)
    )
