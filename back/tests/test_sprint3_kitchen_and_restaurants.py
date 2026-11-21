"""Sprint 3 manager restaurant/menu creation, preparer assignment, kitchen queue, and courier address visibility."""

from uuid import uuid4

import pytest

from conftest import ADDRESS, auth_header, register_and_login
from test_sprint3_delivery import create_cash_order, user_id

pytestmark = pytest.mark.integration


def test_manager_can_create_and_update_restaurants_menu_items_and_staff(
    client, customer, operator, restaurant_manager, courier, order_preparer
):
    create_url = "/api/v1/operations/restaurants"
    payload = {
        "name": "Port Said Grill",
        "category": "grill",
        "kind": "restaurant",
        "address": "23 July St, El Sharq, Port Said",
        "delivery_fee": "15.00",
        "delivery_minutes": 25,
        "description": "Fresh seafood and charcoal grill.",
    }

    # Only global operator/admin can create a new restaurant or link staff.
    assert client.post(create_url, json=payload, headers=customer).status_code == 403
    assert client.post(create_url, json=payload, headers=courier).status_code == 403
    assert client.post(create_url, json=payload, headers=order_preparer).status_code == 403
    assert client.post(create_url, json=payload, headers=restaurant_manager).status_code == 403

    created = client.post(create_url, json=payload, headers=operator)
    assert created.status_code == 201, created.text
    restaurant = created.json()["data"]["restaurant"]
    rid = restaurant["id"]
    assert restaurant["name"] == "Port Said Grill"
    assert restaurant["delivery_fee"] == "15.00"

    # Link restaurant_manager to this newly created restaurant -> now they can edit it and add menu items.
    mgr_id = user_id(client, restaurant_manager)
    linked = client.post(
        f"/api/v1/operations/restaurants/{rid}/staff",
        json={"user_id": mgr_id},
        headers=operator,
    )
    assert linked.status_code == 201, linked.text

    # Reject linking non-staff user (customer).
    cust_id = user_id(client, customer)
    bad_staff = client.post(
        f"/api/v1/operations/restaurants/{rid}/staff",
        json={"user_id": cust_id},
        headers=operator,
    )
    assert bad_staff.status_code == 400 and bad_staff.json()["error"]["code"] == "invalid_staff_role"

    # Linked manager updates restaurant info and adds a menu item.
    patched_rest = client.patch(
        f"/api/v1/operations/restaurants/{rid}",
        json={"delivery_minutes": 20, "delivery_fee": "12.50"},
        headers=restaurant_manager,
    )
    assert patched_rest.status_code == 200
    assert patched_rest.json()["data"]["restaurant"]["time"] == 20

    item_res = client.post(
        f"/api/v1/operations/restaurants/{rid}/menu-items",
        json={
            "name": "Mixed Grill Platter",
            "category": "Main",
            "price": "185.00",
            "description": "Kofta and shish tawook",
        },
        headers=restaurant_manager,
    )
    assert item_res.status_code == 201, item_res.text
    item_id = item_res.json()["data"]["item"]["id"]

    updated_item = client.patch(
        f"/api/v1/operations/restaurants/{rid}/menu-items/{item_id}",
        json={"price": "195.00", "is_available": True},
        headers=restaurant_manager,
    )
    assert updated_item.status_code == 200
    assert updated_item.json()["data"]["item"]["price"] == "195.00"

    # Newly added restaurant and menu item appear immediately in public catalog.
    public_list = client.get("/api/v1/restaurants?search=Port+Said+Grill").json()["data"][
        "restaurants"
    ]
    assert any(r["id"] == rid for r in public_list)
    public_menu = client.get(f"/api/v1/restaurants/{rid}/menu").json()["data"]["menu"]
    assert [m["name"] for m in public_menu] == ["Mixed Grill Platter"]


def test_preparer_assignment_kitchen_flow_and_courier_structured_address(
    client,
    customer,
    restaurant_manager,
    order_preparer,
    other_preparer,
    courier,
    address,
):
    order = create_cash_order(client, customer, address)
    preparer_id = user_id(client, order_preparer)
    courier_id = user_id(client, courier)

    # Preparer directory lists active preparers for this restaurant.
    preparers = client.get(
        f"/api/v1/operations/preparers?restaurant_id={order['restaurant_id']}",
        headers=restaurant_manager,
    ).json()["data"]["preparers"]
    assert [p["id"] for p in preparers] == [preparer_id]

    # Before acceptance, assigning a preparer fails -> 409.
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/preparer-assignment",
            json={"preparer_id": preparer_id},
            headers=restaurant_manager,
        ).status_code
        == 409
    )

    # Manager accepts order -> REST preparer receives notification, Market preparer does NOT.
    assert (
        client.patch(
            f"/api/v1/operations/orders/{order['id']}/status",
            json={"status": "accepted"},
            headers=restaurant_manager,
        ).status_code
        == 200
    )
    prep_notifs = client.get("/api/v1/notifications", headers=order_preparer).json()["data"][
        "notifications"
    ]
    assert [n["event_type"] for n in prep_notifs] == ["order_assigned_to_preparer"]
    assert client.get("/api/v1/notifications", headers=other_preparer).json()["data"]["notifications"] == []

    # Manager explicitly assigns order_preparer + assigns courier.
    assigned_prep = client.post(
        f"/api/v1/orders/{order['id']}/preparer-assignment",
        json={"preparer_id": preparer_id},
        headers=restaurant_manager,
    )
    assert assigned_prep.status_code == 200, assigned_prep.text
    assert assigned_prep.json()["data"]["order"]["assigned_preparer"]["id"] == preparer_id
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/delivery-assignment",
            json={"delivery_person_id": courier_id},
            headers=restaurant_manager,
        ).status_code
        == 201
    )

    # Assigned preparer sees order in kitchen queue; other_preparer does NOT and cannot mutate it.
    kitchen_list = client.get("/api/v1/kitchen/orders", headers=order_preparer).json()["data"][
        "orders"
    ]
    assert [o["id"] for o in kitchen_list] == [order["id"]]
    assert client.get("/api/v1/kitchen/orders", headers=other_preparer).json()["data"]["orders"] == []
    assert (
        client.patch(
            f"/api/v1/kitchen/orders/{order['id']}/status",
            json={"status": "preparing"},
            headers=other_preparer,
        ).status_code
        == 403
    )

    # Preparer cannot submit invalid/non-kitchen statuses.
    assert (
        client.patch(
            f"/api/v1/kitchen/orders/{order['id']}/status",
            json={"status": "delivered"},
            headers=order_preparer,
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/kitchen/orders/{order['id']}/status",
            json={"status": "ready_for_pickup"},
            headers=order_preparer,
        ).status_code
        == 409
    )

    # Preparer starts preparing, then confirms ready_for_pickup -> Courier & Customer both notified!
    prep_res = client.patch(
        f"/api/v1/kitchen/orders/{order['id']}/status",
        json={"status": "preparing"},
        headers=order_preparer,
    )
    assert prep_res.status_code == 200 and prep_res.json()["data"]["order"]["status"] == "preparing"

    ready_res = client.patch(
        f"/api/v1/kitchen/orders/{order['id']}/status",
        json={"status": "ready_for_pickup", "note": "Packed and sealed"},
        headers=order_preparer,
    )
    assert ready_res.status_code == 200 and ready_res.json()["data"]["order"]["status"] == "ready_for_pickup"

    # Courier receives both delivery_assigned AND order_ready_for_courier_pickup notifications.
    courier_notifs = client.get("/api/v1/notifications", headers=courier).json()["data"][
        "notifications"
    ]
    assert [n["event_type"] for n in reversed(courier_notifs)] == [
        "delivery_assigned",
        "order_ready_for_courier_pickup",
    ]

    # Courier's my-orders returns complete structured customer address + restaurant pickup info.
    my_orders = client.get("/api/v1/delivery/my-orders", headers=courier).json()["data"]["orders"]
    assert len(my_orders) == 1
    d_addr = my_orders[0]["delivery_address"]
    assert d_addr["recipient_name"] == ADDRESS["recipient_name"]
    assert d_addr["phone"] == ADDRESS["phone"]
    assert d_addr["city"] == ADDRESS["city"]
    assert d_addr["area"] == ADDRESS["area"]
    assert d_addr["street"] == ADDRESS["street"]
    assert d_addr["building"] == ADDRESS["building"]
    assert d_addr["floor"] == ADDRESS["floor"]
    assert d_addr["apartment"] == ADDRESS["apartment"]
    assert d_addr["delivery_notes"] == ADDRESS["delivery_notes"]
    assert my_orders[0]["restaurant_name"] == "Test Burger"
    assert my_orders[0]["restaurant_address"] == "Cairo"

    # Courier completes pickup and delivery.
    assert (
        client.patch(
            f"/api/v1/delivery/orders/{order['id']}/status",
            json={"status": "PICKED_UP"},
            headers=courier,
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/delivery/orders/{order['id']}/status",
            json={"status": "DELIVERED"},
            headers=courier,
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]["status"] == "delivered"
