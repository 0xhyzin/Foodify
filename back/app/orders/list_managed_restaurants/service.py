"""Resolve restaurants accessible to an operational actor."""

from app.infrastructure.models import User
from app.ordering.shared.guards import is_global_operator
from app.ordering.shared.interfaces import RestaurantStaffRepository
from app.ordering.shared.mappers import restaurant_view
from app.orders.list_managed_restaurants.dto import (
    ManagedRestaurantsData,
    ManagedRestaurantsResponse,
)


class ListManagedRestaurantsService:
    def __init__(self, staff: RestaurantStaffRepository) -> None:
        self.staff = staff

    def execute(self, actor: User) -> ManagedRestaurantsResponse:
        items = (
            self.staff.list_all_active_restaurants()
            if is_global_operator(actor)
            else self.staff.list_managed_restaurants(actor.id)
        )
        return ManagedRestaurantsResponse(
            data=ManagedRestaurantsData(restaurants=[restaurant_view(item) for item in items])
        )
