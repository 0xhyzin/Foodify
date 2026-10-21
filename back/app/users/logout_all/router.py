"""The authenticated all-sessions logout HTTP endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_current_user
from app.infrastructure.models import User
from app.users.logout_all.dependencies import get_service
from app.users.logout_all.dto import LogoutAllRequest
from app.users.logout_all.interfaces import LogoutAllServiceInterface

router = APIRouter()
Service = Annotated[LogoutAllServiceInterface, Depends(get_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/logout-all", status_code=204)
def logout_all_sessions(service: Service, current_user: CurrentUser) -> Response:
    service.execute(LogoutAllRequest(user_id=current_user.id))
    return Response(status_code=204)
