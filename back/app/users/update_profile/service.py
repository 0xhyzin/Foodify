"""Apply explicitly provided customer profile changes."""

from app.shared.ports import UnitOfWork
from app.users.shared.dto.profile import user_response
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import UserRepository
from app.users.update_profile.dto import UpdateProfileRequest, UpdateProfileResponse


class UpdateProfileService:
    def __init__(self, users: UserRepository, uow: UnitOfWork) -> None:
        self.users = users
        self.uow = uow

    def execute(self, user_id: str, payload: UpdateProfileRequest) -> UpdateProfileResponse:
        user = require_active_user(self.users, user_id, for_update=True)
        if "name" in payload.model_fields_set:
            user.name = payload.name
        if "phone" in payload.model_fields_set:
            user.phone = payload.phone
        self.uow.commit()
        return UpdateProfileResponse.model_validate(user_response(user))
