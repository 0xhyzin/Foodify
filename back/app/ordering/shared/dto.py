"""Typed public views shared by ordering operations; Decimal stays exact in JSON."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.shared.dto import APIModel
from app.users.shared.dto.address import AddressWriteRequest

Quantity = Annotated[int, Field(strict=True, ge=1, le=99)]


class Pagination(APIModel):
    limit: int
    offset: int
    has_more: bool


class RestaurantView(APIModel):
    id: str
    name: str
    category: str
    rating: Decimal
    reviews: int
    time: int
    address: str
    image: str | None
    description: str | None
    delivery_fee: Decimal
    kind: str
    slug: str | None
    logo: str | None
    artwork: str
    tags: list[str]


class RestaurantDetail(RestaurantView):
    categories: list[str]


class MenuItemView(APIModel):
    id: str
    restaurant_id: str
    name: str
    category: str
    price: Decimal
    desc: str | None
    image: str | None
    available: bool
    artwork: str


class CartLineView(APIModel):
    id: str
    menu_item_id: str
    name: str
    price: Decimal
    quantity: int
    line_total: Decimal
    image: str | None
    available: bool


class CartView(APIModel):
    id: str | None
    restaurant_id: str | None
    items: list[CartLineView]
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    currency: str = "EGP"
    revision: int = 0


class CartData(APIModel):
    cart: CartView


class CartResponse(APIModel):
    data: CartData


class OrderLineView(APIModel):
    menu_item_id: str
    name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class PaymentView(APIModel):
    provider: str
    status: str
    amount: Decimal
    reference: str
    is_simulated: bool
    claimed_reference: str | None = None
    transfer_recipient: str | None = None
    transfer_recipient_name: str | None = None


class OrderView(APIModel):
    id: str
    restaurant_id: str
    address_id: str | None
    delivery_address: AddressWriteRequest
    status: str
    payment_method: str
    payment_status: str
    payment: PaymentView | None
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    currency: str
    created_at: datetime
    items: list[OrderLineView]
    events: list["OrderEventView"] = Field(default_factory=list)


class OrderEventView(APIModel):
    status: str
    note: str | None
    created_at: datetime


class OrderListData(APIModel):
    orders: list[OrderView]
    pagination: Pagination


class OrderListResponse(APIModel):
    data: OrderListData
