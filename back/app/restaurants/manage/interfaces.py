"""Boundary for restaurant, menu, and staff management."""

from typing import Protocol

from app.infrastructure.models import User

from .dto import (
    AssignRestaurantStaffRequest,
    AssignStaffResponse,
    CreateMenuItemRequest,
    CreateRestaurantRequest,
    ManageMenuItemResponse,
    ManageRestaurantResponse,
    UpdateMenuItemRequest,
    UpdateRestaurantRequest,
)


class ManageRestaurantsServiceInterface(Protocol):
    def create_restaurant(
        self, actor: User, payload: CreateRestaurantRequest
    ) -> ManageRestaurantResponse: ...

    def update_restaurant(
        self, actor: User, restaurant_id: str, payload: UpdateRestaurantRequest
    ) -> ManageRestaurantResponse: ...

    def create_menu_item(
        self, actor: User, restaurant_id: str, payload: CreateMenuItemRequest
    ) -> ManageMenuItemResponse: ...

    def update_menu_item(
        self, actor: User, restaurant_id: str, item_id: str, payload: UpdateMenuItemRequest
    ) -> ManageMenuItemResponse: ...

    def assign_staff(
        self, actor: User, restaurant_id: str, payload: AssignRestaurantStaffRequest
    ) -> AssignStaffResponse: ...
