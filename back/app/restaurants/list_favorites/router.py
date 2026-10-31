from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.restaurants.shared.dto import FavoritesResponse

from .dependencies import get_service
from .interfaces import ListFavoritesServiceInterface

router = APIRouter(tags=["Catalog"])


@router.get("/users/me/favorites", response_model=FavoritesResponse)
def list_favorites(
    service: Annotated[ListFavoritesServiceInterface, Depends(get_service)],
    user: Annotated[User, Depends(require_permission("profile:read"))],
) -> FavoritesResponse:
    return service.execute(user.id)
