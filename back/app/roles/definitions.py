"""Idempotent seed data; permissions are normalized in role_permissions.

Sprint 2 uses order creation, own-history, and operations-management permissions.
Delivery assignment and staff-management vocabulary is reserved for later features.
"""

from app.roles.enums import RoleType

ROLE_NAMES: dict[RoleType, str] = {
    RoleType.CUSTOMER: "Customer",
    RoleType.COURIER: "Courier",
    RoleType.ORDER_PREPARER: "Order preparer",
    RoleType.OPERATIONS_MANAGER: "Operations manager",
    RoleType.ADMIN: "Administrator",
}

PERMISSION_NAMES: dict[str, str] = {
    "profile:read": "Read own profile",
    "profile:write": "Update own profile",
    "addresses:manage": "Manage own delivery addresses",
    "orders:create": "Place an order",
    "orders:read_own": "Read own orders",
    "deliveries:read_assigned": "Read assigned deliveries",
    "deliveries:update_assigned": "Update assigned deliveries",
    "orders:read": "Read operational orders",
    "orders:prepare": "Prepare orders",
    "orders:manage": "Manage operational orders",
    "payments:review": "Verify received manual transfers against bank records",
    "deliveries:assign": "Assign deliveries",
    "staff:read": "Read staff directory",
    "staff:manage": "Create and manage staff accounts",
    "roles:manage": "Manage staff roles and permissions",
}

_SELF_SERVICE_PERMISSIONS = frozenset(
    {
        "profile:read",
        "profile:write",
        "addresses:manage",
    }
)

ROLE_PERMISSIONS: dict[RoleType, frozenset[str]] = {
    RoleType.CUSTOMER: _SELF_SERVICE_PERMISSIONS
    | {
        "orders:create",
        "orders:read_own",
    },
    RoleType.COURIER: _SELF_SERVICE_PERMISSIONS
    | {
        "deliveries:read_assigned",
        "deliveries:update_assigned",
    },
    RoleType.ORDER_PREPARER: _SELF_SERVICE_PERMISSIONS
    | {
        "orders:read",
        "orders:prepare",
    },
    RoleType.OPERATIONS_MANAGER: _SELF_SERVICE_PERMISSIONS
    | {
        "orders:read",
        "orders:manage",
        "payments:review",
        "deliveries:assign",
        "staff:read",
    },
    RoleType.ADMIN: frozenset(PERMISSION_NAMES),
}
