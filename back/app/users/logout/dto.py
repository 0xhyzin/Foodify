"""Internal logout input populated from the Authorization header."""

from app.shared.dto import APIModel


class LogoutRequest(APIModel):
    access_token: str
