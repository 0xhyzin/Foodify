"""HTTP presentation for reset_password only."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.users.reset_password.dependencies import get_service
from app.users.reset_password.dto import ResetPasswordRequest, ResetPasswordResponse
from app.users.reset_password.interfaces import ResetPasswordServiceInterface

router = APIRouter()


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=200)
def reset_customer_password(
    payload: ResetPasswordRequest,
    service: Annotated[ResetPasswordServiceInterface, Depends(get_service)],
) -> ResetPasswordResponse:
    service.execute(payload)
    return ResetPasswordResponse(message="Password changed. Sign in again on your devices.")
