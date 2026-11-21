"""Operational endpoints for adding/updating restaurants, menus, and staff."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import require_permission
from app.infrastructure.models import User

from .dependencies import get_service
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
from .interfaces import ManageRestaurantsServiceInterface

router = APIRouter(tags=["Operations restaurants"])
Manager = Annotated[User, Depends(require_permission("orders:manage"))]
Service = Annotated[ManageRestaurantsServiceInterface, Depends(get_service)]


@router.post(
    "/operations/restaurants",
    response_model=ManageRestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant(
    payload: CreateRestaurantRequest,
    actor: Manager,
    service: Service,
) -> ManageRestaurantResponse:
    return service.create_restaurant(actor, payload)


@router.patch(
    "/operations/restaurants/{restaurant_id}",
    response_model=ManageRestaurantResponse,
)
def update_restaurant(
    restaurant_id: UUID,
    payload: UpdateRestaurantRequest,
    actor: Manager,
    service: Service,
) -> ManageRestaurantResponse:
    return service.update_restaurant(actor, str(restaurant_id), payload)


@router.post(
    "/operations/restaurants/{restaurant_id}/menu-items",
    response_model=ManageMenuItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item(
    restaurant_id: UUID,
    payload: CreateMenuItemRequest,
    actor: Manager,
    service: Service,
) -> ManageMenuItemResponse:
    return service.create_menu_item(actor, str(restaurant_id), payload)


@router.patch(
    "/operations/restaurants/{restaurant_id}/menu-items/{item_id}",
    response_model=ManageMenuItemResponse,
)
def update_menu_item(
    restaurant_id: UUID,
    item_id: UUID,
    payload: UpdateMenuItemRequest,
    actor: Manager,
    service: Service,
) -> ManageMenuItemResponse:
    return service.update_menu_item(actor, str(restaurant_id), str(item_id), payload)


@router.post(
    "/operations/restaurants/{restaurant_id}/staff",
    response_model=AssignStaffResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_restaurant_staff(
    restaurant_id: UUID,
    payload: AssignRestaurantStaffRequest,
    actor: Manager,
    service: Service,
) -> AssignStaffResponse:
    return service.assign_staff(actor, str(restaurant_id), payload)
