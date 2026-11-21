"""DTO contracts for managing restaurants, menus, and staff assignments."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.ordering.shared.dto import MenuItemView, RestaurantView
from app.shared.dto import APIModel

MerchantKind = Literal["restaurant", "dessert", "grocery"]


class CreateRestaurantRequest(APIModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    kind: MerchantKind = "restaurant"
    address: str = Field(min_length=3, max_length=300)
    delivery_fee: Decimal = Field(default=Decimal("0.00"), ge=0, le=5000)
    delivery_minutes: int = Field(default=35, ge=5, le=180)
    description: str | None = Field(default=None, max_length=1000)
    artwork: str = Field(default="burger", max_length=2048)
    image: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class UpdateRestaurantRequest(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    kind: MerchantKind | None = None
    address: str | None = Field(default=None, min_length=3, max_length=300)
    delivery_fee: Decimal | None = Field(default=None, ge=0, le=5000)
    delivery_minutes: int | None = Field(default=None, ge=5, le=180)
    description: str | None = Field(default=None, max_length=1000)
    artwork: str | None = Field(default=None, max_length=2048)
    image: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CreateMenuItemRequest(APIModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=100)
    price: Decimal = Field(ge=0, le=50000)
    description: str | None = Field(default=None, max_length=1000)
    artwork: str = Field(default="burger", max_length=2048)
    image: str | None = Field(default=None, max_length=500)
    is_available: bool = True


class UpdateMenuItemRequest(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    price: Decimal | None = Field(default=None, ge=0, le=50000)
    description: str | None = Field(default=None, max_length=1000)
    artwork: str | None = Field(default=None, max_length=2048)
    image: str | None = Field(default=None, max_length=500)
    is_available: bool | None = None


class AssignRestaurantStaffRequest(APIModel):
    user_id: UUID


class RestaurantData(APIModel):
    restaurant: RestaurantView


class ManageRestaurantResponse(APIModel):
    data: RestaurantData


class MenuItemData(APIModel):
    item: MenuItemView


class ManageMenuItemResponse(APIModel):
    data: MenuItemData


class AssignStaffData(APIModel):
    restaurant_id: str
    user_id: str


class AssignStaffResponse(APIModel):
    data: AssignStaffData
