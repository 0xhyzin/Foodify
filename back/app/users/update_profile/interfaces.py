"""Update-profile application boundary."""

from typing import Protocol

from app.users.update_profile.dto import UpdateProfileRequest, UpdateProfileResponse


class UpdateProfileServiceInterface(Protocol):
    def execute(self, user_id: str, payload: UpdateProfileRequest) -> UpdateProfileResponse: ...
