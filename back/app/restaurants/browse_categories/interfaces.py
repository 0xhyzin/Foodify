from typing import Protocol

from .dto import CategoryResponse


class BrowseCategoriesServiceInterface(Protocol):
    def execute(self) -> CategoryResponse: ...
