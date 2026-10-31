from typing import Annotated

from fastapi import APIRouter, Depends

from .dependencies import get_service
from .dto import CategoryResponse
from .interfaces import BrowseCategoriesServiceInterface

router = APIRouter(tags=["Catalog"])


@router.get("/catalog/categories", response_model=CategoryResponse)
def browse_categories(
    service: Annotated[BrowseCategoriesServiceInterface, Depends(get_service)],
) -> CategoryResponse:
    return service.execute()
