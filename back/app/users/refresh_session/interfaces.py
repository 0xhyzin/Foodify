"""The refresh route's application boundary."""

from typing import Protocol

from app.users.refresh_session.dto import RefreshRequest, RefreshResponse


class RefreshSessionServiceInterface(Protocol):
    def execute(self, payload: RefreshRequest) -> RefreshResponse: ...
