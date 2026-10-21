"""The login route depends only on its own application boundary."""

from typing import Protocol

from app.users.login.dto import LoginRequest, LoginResponse


class LoginServiceInterface(Protocol):
    def execute(self, payload: LoginRequest) -> LoginResponse: ...
