"""HTTP endpoint for editing the authenticated customer's profile."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.update_profile.dependencies import get_service
from app.users.update_profile.dto import UpdateProfileRequest, UpdateProfileResponse
from app.users.update_profile.interfaces import UpdateProfileServiceInterface

router = APIRouter(tags=["Customer profile"])
ProfileWriter = Annotated[User, Depends(require_permission("profile:write"))]
ProfileService = Annotated[UpdateProfileServiceInterface, Depends(get_service)]


@router.patch("/me", response_model=UpdateProfileResponse)
def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: ProfileWriter,
    service: ProfileService,
) -> UpdateProfileResponse:
    """Change the display name or E.164 phone; null phone clears it."""
    return service.execute(current_user.id, payload)
