"""Profile response returned after selecting a default delivery address."""

from app.users.shared.dto.profile import UserResponse


class SetDefaultAddressResponse(UserResponse):
    """The customer profile with its current default-address identifier."""
