"""HTTP endpoint for reading the authenticated customer's profile."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.get_profile.dependencies import get_service
from app.users.get_profile.dto import GetProfileResponse
from app.users.get_profile.interfaces import GetProfileServiceInterface

router = APIRouter(tags=["Customer profile"])
ProfileReader = Annotated[User, Depends(require_permission("profile:read"))]
ProfileService = Annotated[GetProfileServiceInterface, Depends(get_service)]


@router.get("/me", response_model=GetProfileResponse)
def get_my_profile(current_user: ProfileReader, service: ProfileService) -> GetProfileResponse:
    """Read the authenticated user's profile and completion status."""
    return service.execute(current_user.id)
