"""The password login HTTP endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import limit_email_action
from app.users.login.dependencies import get_service
from app.users.login.dto import LoginRequest, LoginResponse
from app.users.login.interfaces import LoginServiceInterface

router = APIRouter()
Service = Annotated[LoginServiceInterface, Depends(get_service)]


@router.post("/login", response_model=LoginResponse)
def login_customer(payload: LoginRequest, service: Service) -> LoginResponse:
    limit_email_action("login", payload.email, limit=10)
    return service.execute(payload)
