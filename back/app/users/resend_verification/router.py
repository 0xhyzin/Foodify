"""HTTP presentation for resend_verification only."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import limit_email_action
from app.users.resend_verification.dependencies import get_service
from app.users.resend_verification.dto import ResendVerificationRequest, ResendVerificationResponse
from app.users.resend_verification.interfaces import ResendVerificationServiceInterface
from app.users.shared.dto.messages import GENERIC_EMAIL_MESSAGE

router = APIRouter()


@router.post("/resend-verification", response_model=ResendVerificationResponse, status_code=202)
def resend_email_verification(
    payload: ResendVerificationRequest,
    service: Annotated[ResendVerificationServiceInterface, Depends(get_service)],
) -> ResendVerificationResponse:
    limit_email_action("resend_verification", payload.email)
    service.execute(payload)
    return ResendVerificationResponse(message=GENERIC_EMAIL_MESSAGE)
