"""The refresh token rotation HTTP endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.users.refresh_session.dependencies import get_service
from app.users.refresh_session.dto import RefreshRequest, RefreshResponse
from app.users.refresh_session.interfaces import RefreshSessionServiceInterface

router = APIRouter()
Service = Annotated[RefreshSessionServiceInterface, Depends(get_service)]


@router.post("/refresh", response_model=RefreshResponse)
def rotate_session_tokens(payload: RefreshRequest, service: Service) -> RefreshResponse:
    return service.execute(payload)
