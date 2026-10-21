"""The authenticated current-session logout HTTP endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_bearer_token, get_current_user
from app.infrastructure.models import User
from app.users.logout.dependencies import get_service
from app.users.logout.dto import LogoutRequest
from app.users.logout.interfaces import LogoutServiceInterface

router = APIRouter()
Service = Annotated[LogoutServiceInterface, Depends(get_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/logout", status_code=204)
def logout_current_session(
    service: Service,
    current_user: CurrentUser,
    token: Annotated[str, Depends(get_bearer_token)],
) -> Response:
    service.execute(LogoutRequest(access_token=token))
    return Response(status_code=204)
