"""Business boundary for register."""

from typing import Protocol

from app.users.register.dto import RegisterRequest


class RegisterServiceInterface(Protocol):
    def execute(self, payload: RegisterRequest) -> None: ...
