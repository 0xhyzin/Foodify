"""The browser logout operation's application boundary."""

from typing import Protocol

from app.users.browser.logout.dto import BrowserLogoutRequest


class BrowserLogoutServiceInterface(Protocol):
    def execute(self, payload: BrowserLogoutRequest) -> None: ...
