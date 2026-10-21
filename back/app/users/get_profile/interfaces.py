"""Get-profile application boundary."""

from typing import Protocol

from app.users.get_profile.dto import GetProfileResponse


class GetProfileServiceInterface(Protocol):
    def execute(self, user_id: str) -> GetProfileResponse: ...
