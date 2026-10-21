"""Internal logout input populated from the authenticated customer."""

from app.shared.dto import APIModel


class LogoutAllRequest(APIModel):
    user_id: str
