"""Stable machine-readable role codes."""

from enum import StrEnum


class RoleType(StrEnum):
    CUSTOMER = "customer"
    COURIER = "courier"
    ORDER_PREPARER = "order_preparer"
    OPERATIONS_MANAGER = "operations_manager"
    ADMIN = "admin"
