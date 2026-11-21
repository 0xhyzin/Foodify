"""Stable machine-readable role codes."""

from enum import StrEnum


class RoleType(StrEnum):
    CUSTOMER = "customer"
    COURIER = "courier"
    ORDER_PREPARER = "order_preparer"
    RESTAURANT_MANAGER = "restaurant_manager"
    OPERATIONS_MANAGER = "operations_manager"
    ADMIN = "admin"
