from typing import Protocol

from .dto import CartListResponse


class ListCartsServiceInterface(Protocol):
    def execute(self, user_id: str, limit: int = 100, offset: int = 0) -> CartListResponse: ...
