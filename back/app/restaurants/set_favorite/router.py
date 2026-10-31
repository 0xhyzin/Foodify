from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.restaurants.shared.dto import FavoritesResponse

from .dependencies import get_service
from .dto import FavoriteRequest
from .interfaces import SetFavoriteServiceInterface

router = APIRouter(tags=["Catalog"])


@router.put("/users/me/favorites/{restaurant_id}", response_model=FavoritesResponse)
def set_favorite(
    service: Annotated[SetFavoriteServiceInterface, Depends(get_service)],
    user: Annotated[User, Depends(require_permission("profile:read"))],
    restaurant_id: UUID,
    payload: FavoriteRequest,
) -> FavoritesResponse:
    return service.execute(user.id, str(restaurant_id), payload)
