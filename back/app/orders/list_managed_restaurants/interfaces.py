"""Boundary for listing restaurants authorized for operational access."""

from typing import Protocol

from app.infrastructure.models import User
from app.orders.list_managed_restaurants.dto import ManagedRestaurantsResponse


class ListManagedRestaurantsServiceInterface(Protocol):
    def execute(self, actor: User) -> ManagedRestaurantsResponse: ...
