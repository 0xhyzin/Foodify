"""The current-session logout application's boundary."""

from typing import Protocol

from app.users.logout.dto import LogoutRequest


class LogoutServiceInterface(Protocol):
    def execute(self, payload: LogoutRequest) -> None: ...
