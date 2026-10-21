"""Read the profile of an active customer."""

from app.users.get_profile.dto import GetProfileResponse
from app.users.shared.dto.profile import user_response
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import UserRepository


class GetProfileService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def execute(self, user_id: str) -> GetProfileResponse:
        user = require_active_user(self.users, user_id)
        return GetProfileResponse.model_validate(user_response(user))
