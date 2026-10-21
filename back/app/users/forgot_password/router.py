"""HTTP presentation for forgot_password only."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import limit_email_action
from app.users.forgot_password.dependencies import get_service
from app.users.forgot_password.dto import ForgotPasswordRequest, ForgotPasswordResponse
from app.users.forgot_password.interfaces import ForgotPasswordServiceInterface
from app.users.shared.dto.messages import GENERIC_EMAIL_MESSAGE

router = APIRouter()


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=202)
def request_password_reset(
    payload: ForgotPasswordRequest,
    service: Annotated[ForgotPasswordServiceInterface, Depends(get_service)],
) -> ForgotPasswordResponse:
    limit_email_action("forgot_password", payload.email)
    service.execute(payload)
    return ForgotPasswordResponse(message=GENERIC_EMAIL_MESSAGE)
