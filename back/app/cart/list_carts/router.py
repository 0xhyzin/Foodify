from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
from .dto import CartListResponse
from .interfaces import ListCartsServiceInterface

router = APIRouter(tags=["Customer cart"])


@router.get("/carts", response_model=CartListResponse)
def list_my_carts(
    user: Annotated[User, Depends(require_permission("orders:create"))],
    service: Annotated[ListCartsServiceInterface, Depends(get_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> CartListResponse:
    return service.execute(user.id, limit, offset)
