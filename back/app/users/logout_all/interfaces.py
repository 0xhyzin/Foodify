"""The all-sessions logout application boundary."""

from typing import Protocol

from app.users.logout_all.dto import LogoutAllRequest


class LogoutAllServiceInterface(Protocol):
    def execute(self, payload: LogoutAllRequest) -> None: ...
