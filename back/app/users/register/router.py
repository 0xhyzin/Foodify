"""HTTP presentation for register only."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import limit_email_action
from app.users.register.dependencies import get_service
from app.users.register.dto import RegisterRequest, RegisterResponse
from app.users.register.interfaces import RegisterServiceInterface
from app.users.shared.dto.messages import GENERIC_EMAIL_MESSAGE

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=202)
def register_customer(
    payload: RegisterRequest, service: Annotated[RegisterServiceInterface, Depends(get_service)]
) -> RegisterResponse:
    limit_email_action("register", payload.email)
    service.execute(payload)
    return RegisterResponse(message=GENERIC_EMAIL_MESSAGE)
