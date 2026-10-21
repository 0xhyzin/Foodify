"""Response owned by the get-profile operation."""

from app.users.shared.dto.profile import UserResponse


class GetProfileResponse(UserResponse):
    """Profile, role permissions, and delivery completion status."""
