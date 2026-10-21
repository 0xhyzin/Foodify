"""Request validation and response for updating a customer profile."""

from typing import Self

from pydantic import model_validator

from app.shared.dto import APIModel
from app.users.shared.dto.primitives import PersonName, PhoneNumber
from app.users.shared.dto.profile import UserResponse


class UpdateProfileRequest(APIModel):
    name: PersonName | None = None
    phone: PhoneNumber | None = None

    @model_validator(mode="after")
    def require_profile_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide a name or phone number to update.")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Name cannot be null.")
        return self


class UpdateProfileResponse(UserResponse):
    """The customer's profile after applying the requested changes."""
