"""Logout receives its credential only from the HttpOnly browser cookie."""

from app.shared.dto import APIModel


class BrowserLogoutRequest(APIModel):
    refresh_token: str | None
