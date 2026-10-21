"""HTTP presentation for verify_email only."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.users.verify_email.dependencies import get_service
from app.users.verify_email.dto import VerifyEmailRequest, VerifyEmailResponse
from app.users.verify_email.interfaces import VerifyEmailServiceInterface

router = APIRouter()


@router.post("/verify-email", response_model=VerifyEmailResponse, status_code=200)
def confirm_customer_email(
    payload: VerifyEmailRequest,
    service: Annotated[VerifyEmailServiceInterface, Depends(get_service)],
) -> VerifyEmailResponse:
    service.execute(payload)
    return VerifyEmailResponse(message="Email confirmed. You can now sign in.")
