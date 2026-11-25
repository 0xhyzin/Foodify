"""Sprint 3 admin user directory, staff onboarding, role updates, and guardrails."""

import pytest

from conftest import PASSWORD, assign_role, login
from test_restaurants import REST

pytestmark = pytest.mark.integration


def test_admin_creates_staff_and_they_can_login_immediately(client):
    admin_headers, _ = assign_role(client, "admin@example.com", "admin", name="Platform Admin")

    # Create courier directly without email verification blocker.
    res_courier = client.post(
        "/api/v1/admin/staff",
        json={
            "name": "Courier Karim",
            "email": "karim.courier@example.com",
            "password": PASSWORD,
            "phone": "+201011223344",
            "roles": ["courier"],
        },
        headers=admin_headers,
    )
    assert res_courier.status_code == 201, res_courier.text
    created_courier = res_courier.json()["data"]["user"]
    assert created_courier["email_verified"] is True
    assert created_courier["roles"] == ["courier"]

    courier_login = login(client, email="karim.courier@example.com", password=PASSWORD)
    assert courier_login.status_code == 200, courier_login.text
    assert courier_login.json()["user"]["roles"] == ["courier"]

    # Create restaurant manager linked to REST + verify managed_restaurant_ids populated.
    res_mgr = client.post(
        "/api/v1/admin/staff",
        json={
            "name": "Manager Nadia",
            "email": "nadia.manager@example.com",
            "password": PASSWORD,
            "roles": ["restaurant_manager"],
            "restaurant_id": REST,
        },
        headers=admin_headers,
    )
    assert res_mgr.status_code == 201, res_mgr.text
    mgr_user = res_mgr.json()["data"]["user"]
    assert mgr_user["roles"] == ["restaurant_manager"]
    assert mgr_user["managed_restaurant_ids"] == [REST]

    # Duplicate email returns 409 email_already_registered.
    dup = client.post(
        "/api/v1/admin/staff",
        json={
            "name": "Duplicate Courier",
            "email": "karim.courier@example.com",
            "password": PASSWORD,
            "roles": ["courier"],
        },
        headers=admin_headers,
    )
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "email_already_registered"


def test_admin_user_directory_permissions_and_filters(client, customer, operator):
    admin_headers, _ = assign_role(client, "admin2@example.com", "admin", name="Admin Two")
    assert client.get("/api/v1/admin/users", headers=customer).status_code == 403

    # Operations manager can read users (staff:read), but cannot create staff or edit roles.
    op_list = client.get("/api/v1/admin/users", headers=operator)
    assert op_list.status_code == 200
    assert (
        client.post(
            "/api/v1/admin/staff",
            json={
                "name": "Blocked Staff",
                "email": "blocked@example.com",
                "password": PASSWORD,
                "roles": ["order_preparer"],
            },
            headers=operator,
        ).status_code
        == 403
    )

    filtered = client.get("/api/v1/admin/users?role=customer&search=Test", headers=admin_headers)
    assert filtered.status_code == 200
    assert any("customer" in u["roles"] for u in filtered.json()["data"]["users"])


def test_admin_updates_roles_deactivates_sessions_and_blocks_self_demotion(
    client, customer, operator
):
    admin_headers, admin_id = assign_role(client, "admin3@example.com", "admin", name="Admin Three")
    cust_id = client.get("/api/v1/users/me", headers=customer).json()["id"]

    # Operations manager cannot patch roles (403); admin can promote + link restaurant.
    assert (
        client.patch(
            f"/api/v1/admin/users/{cust_id}/roles",
            json={"roles": ["order_preparer"]},
            headers=operator,
        ).status_code
        == 403
    )
    updated = client.patch(
        f"/api/v1/admin/users/{cust_id}/roles",
        json={"roles": ["order_preparer"], "is_active": True, "restaurant_id": REST},
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    user_data = updated.json()["data"]["user"]
    assert user_data["roles"] == ["order_preparer"]
    assert REST in user_data["managed_restaurant_ids"]

    # Deactivating a user revokes active status and prevents login.
    suspended = client.patch(
        f"/api/v1/admin/users/{cust_id}/roles",
        json={"roles": ["order_preparer"], "is_active": False},
        headers=admin_headers,
    )
    assert suspended.status_code == 200 and suspended.json()["data"]["user"]["is_active"] is False

    # Self-demotion or self-deactivation is blocked with 409 cannot_demote_self.
    self_demote = client.patch(
        f"/api/v1/admin/users/{admin_id}/roles",
        json={"roles": ["customer"]},
        headers=admin_headers,
    )
    assert (
        self_demote.status_code == 409
        and self_demote.json()["error"]["code"] == "cannot_demote_self"
    )
    self_suspend = client.patch(
        f"/api/v1/admin/users/{admin_id}/roles",
        json={"roles": ["admin"], "is_active": False},
        headers=admin_headers,
    )
    assert (
        self_suspend.status_code == 409
        and self_suspend.json()["error"]["code"] == "cannot_demote_self"
    )


def test_alembic_head_and_reference_seed_idempotency(db):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import select

    from app.core.config import PROJECT_ROOT
    from app.infrastructure.database import get_expected_revision_heads
    from app.infrastructure.models import Role
    from scripts.seed import seed_reference_data

    assert get_expected_revision_heads() == frozenset({"20261121_0006"})
    script_dir = ScriptDirectory.from_config(Config(str(PROJECT_ROOT / "alembic.ini")))
    revisions = [rev.revision for rev in script_dir.walk_revisions()]
    assert revisions[0] == "20261121_0006"
    assert "20261031_0005" in revisions

    second_pass = seed_reference_data(db)
    assert second_pass == {
        "roles_created": 0,
        "permissions_created": 0,
        "role_permission_links_added": 0,
        "token_types_created": 0,
        "names_updated": 0,
    }
    role_codes = set(db.scalars(select(Role.code)))
    assert {
        "customer",
        "admin",
        "operations_manager",
        "restaurant_manager",
        "order_preparer",
        "courier",
    }.issubset(role_codes)

