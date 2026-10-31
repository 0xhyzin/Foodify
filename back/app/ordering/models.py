"""Sprint 2 persistence entities; queries live in repository adapters."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.shared.time import utcnow


def new_id() -> str:
    return str(uuid4())


class Restaurant(Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 0 AND 5", name="ck_restaurant_rating"),
        CheckConstraint("reviews >= 0", name="ck_restaurant_reviews"),
        CheckConstraint("delivery_minutes >= 0", name="ck_restaurant_delivery_minutes"),
        CheckConstraint("delivery_fee >= 0", name="ck_restaurant_delivery_fee"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    kind: Mapped[str] = mapped_column(
        String(20), default="restaurant", server_default="restaurant", index=True
    )
    slug: Mapped[str | None] = mapped_column(String(80), unique=True)
    logo: Mapped[str | None] = mapped_column(String(500))
    artwork: Mapped[str] = mapped_column(String(2048), default="burger", server_default="burger")
    categories: Mapped[list["BrowseCategory"]] = relationship(
        secondary="restaurant_categories", lazy="selectin"
    )
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(300))
    image: Mapped[str | None] = mapped_column(String(500))
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0, server_default="0")
    reviews: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    delivery_minutes: Mapped[int] = mapped_column(Integer, default=35, server_default="35")
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_menu_item_price"),
        Index("ix_menu_restaurant_category", "restaurant_id", "category"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    restaurant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(100), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    description: Mapped[str | None] = mapped_column(Text)
    artwork: Mapped[str] = mapped_column(String(2048), default="burger", server_default="burger")
    image: Mapped[str | None] = mapped_column(String(500))
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", index=True
    )


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = (UniqueConstraint("user_id", "restaurant_id", name="uq_cart_user_restaurant"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    restaurant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("restaurants.id", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    items: Mapped[list["CartItem"]] = relationship(cascade="all, delete-orphan", lazy="raise")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_cart_item_quantity"),
        CheckConstraint("quantity <= 99", name="ck_cart_item_max_quantity"),
        UniqueConstraint("cart_id", "menu_item_id", name="uq_cart_menu_item"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    cart_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("carts.id", ondelete="CASCADE"), index=True
    )
    menu_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("menu_items.id", ondelete="RESTRICT")
    )
    quantity: Mapped[int] = mapped_column(Integer)
    menu_item: Mapped[MenuItem] = relationship(lazy="raise")


class FoodOrder(Base):
    __tablename__ = "food_orders"
    __table_args__ = (
        Index("ix_food_orders_user_created", "user_id", "created_at"),
        Index("ix_food_orders_restaurant_created", "restaurant_id", "created_at"),
        UniqueConstraint("user_id", "checkout_key", name="uq_order_user_checkout_key"),
        CheckConstraint("subtotal >= 0 AND delivery_fee >= 0", name="ck_order_amounts"),
        CheckConstraint("total = subtotal + delivery_fee", name="ck_order_total"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    restaurant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("restaurants.id", ondelete="RESTRICT")
    )
    address_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("addresses.id", ondelete="SET NULL")
    )
    delivery_address: Mapped[dict] = mapped_column(JSON)
    checkout_key: Mapped[str | None] = mapped_column(String(36))
    checkout_fingerprint: Mapped[str | None] = mapped_column(String(64))
    cart_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("carts.id", ondelete="SET NULL")
    )
    cart_revision: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="placed", index=True)
    payment_method: Mapped[str] = mapped_column(String(30))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EGP", server_default="EGP")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    items: Mapped[list["FoodOrderItem"]] = relationship(cascade="all, delete-orphan", lazy="raise")
    payment: Mapped["Payment | None"] = relationship(
        cascade="all, delete-orphan", uselist=False, lazy="raise"
    )
    events: Mapped[list["OrderEvent"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderEvent.created_at, OrderEvent.id",
    )


class FoodOrderItem(Base):
    __tablename__ = "food_order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_quantity"),
        CheckConstraint("quantity <= 99", name="ck_order_item_max_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_order_item_price"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("food_orders.id", ondelete="CASCADE"), index=True
    )
    menu_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("menu_items.id", ondelete="RESTRICT")
    )
    item_name: Mapped[str] = mapped_column(String(160))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount >= 0", name="ck_payment_amount"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("food_orders.id", ondelete="CASCADE"), unique=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reference: Mapped[str] = mapped_column(String(80), unique=True, default=new_id)
    provider_order_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    intention_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    checkout_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    transaction_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    claimed_reference: Mapped[str | None] = mapped_column(String(100))
    verified_reference: Mapped[str | None] = mapped_column(String(100), unique=True)
    test_mode: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    transfer_recipient: Mapped[str | None] = mapped_column(String(120))
    transfer_recipient_name: Mapped[str | None] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class BrowseCategory(Base):
    __tablename__ = "browse_categories"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    artwork: Mapped[str] = mapped_column(String(30))


class RestaurantCategory(Base):
    __tablename__ = "restaurant_categories"
    restaurant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True
    )
    category_code: Mapped[str] = mapped_column(
        String(40), ForeignKey("browse_categories.code", ondelete="CASCADE"), primary_key=True
    )


class FavoriteRestaurant(Base):
    __tablename__ = "favorite_restaurants"
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    restaurant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), primary_key=True
    )


class OrderEvent(Base):
    __tablename__ = "order_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("food_orders.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payments.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
