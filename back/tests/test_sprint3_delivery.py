"""Sprint 3 order transitions, restaurant scoping, delivery assignment/reassignment, and cancellation."""

from uuid import uuid4

import pytest

from conftest import auth_header, register_and_login
from test_ordering import BURGER, MILK, add_item, checkout
from test_restaurants import MARKET, REST

pytestmark = pytest.mark.integration


def user_id(client, headers) -> str:
    return client.get("/api/v1/users/me", headers=headers).json()["id"]


def create_cash_order(client, customer, address, restaurant=REST, item=BURGER) -> dict:
    assert add_item(client, customer, restaurant, item, 1).status_code == 201
    cart = client.get(f"/api/v1/carts/{restaurant}", headers=customer).json()["data"]["cart"]
    response = checkout(
        client,
        customer,
        address,
        method="cash",
        cart=cart,
        restaurant_id=restaurant,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["order"]


def advance_to_ready(client, headers, order_id: str) -> dict:
    endpoint = f"/api/v1/operations/orders/{order_id}/status"
    for status in ("accepted", "preparing", "ready_for_pickup"):
        res = client.patch(endpoint, json={"status": status}, headers=headers)
        assert res.status_code == 200, res.text
    return res.json()["data"]["order"]


def test_managed_restaurants_and_cross_restaurant_scoping(
    client, customer, operator, restaurant_manager, other_restaurant_manager, address
):
    order = create_cash_order(client, customer, address, REST, BURGER)

    # Restaurant manager sees only their assigned restaurant; global operator sees both.
    mgr_restaurants = client.get(
        "/api/v1/operations/restaurants", headers=restaurant_manager
    ).json()["data"]["restaurants"]
    assert [r["id"] for r in mgr_restaurants] == [REST]

    op_restaurants = client.get("/api/v1/operations/restaurants", headers=operator).json()["data"][
        "restaurants"
    ]
    assert {r["id"] for r in op_restaurants} == {REST, MARKET}

    # Assigned manager can list and manage their restaurant's order.
    listed = client.get(
        f"/api/v1/restaurant/orders?restaurant_id={REST}", headers=restaurant_manager
    )
    assert listed.status_code == 200 and listed.json()["data"]["orders"][0]["id"] == order["id"]

    # Another restaurant's manager is strictly forbidden on list, status update, and assignment.
    assert (
        client.get(
            f"/api/v1/restaurant/orders?restaurant_id={REST}",
            headers=other_restaurant_manager,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/v1/operations/orders/{order['id']}/status",
            json={"status": "accepted"},
            headers=other_restaurant_manager,
        ).status_code
        == 403
    )

    accepted = client.patch(
        f"/api/v1/operations/orders/{order['id']}/status",
        json={"status": "accepted"},
        headers=restaurant_manager,
    )
    assert accepted.status_code == 200 and accepted.json()["data"]["order"]["status"] == "accepted"


def test_manager_rejection_is_terminal_and_blocks_further_transitions(
    client, customer, restaurant_manager, courier, address
):
    order = create_cash_order(client, customer, address)
    endpoint = f"/api/v1/operations/orders/{order['id']}/status"
    rejected = client.patch(
        endpoint,
        json={"status": "rejected", "note": "Out of stock"},
        headers=restaurant_manager,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["order"]["status"] == "rejected"

    assert (
        client.patch(endpoint, json={"status": "accepted"}, headers=restaurant_manager).status_code
        == 409
    )
    assert (
        client.patch(endpoint, json={"status": "preparing"}, headers=restaurant_manager).status_code
        == 409
    )
    courier_id = user_id(client, courier)
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/delivery-assignment",
            json={"delivery_person_id": courier_id},
            headers=restaurant_manager,
        ).status_code
        == 409
    )


def test_delivery_assignment_validation_and_duplicate_guards(
    client, customer, restaurant_manager, other_restaurant_manager, courier, address
):
    order = create_cash_order(client, customer, address)
    courier_id = user_id(client, courier)
    customer_id = user_id(client, customer)
    assign_url = f"/api/v1/orders/{order['id']}/delivery-assignment"

    # Unauthenticated and unauthorized roles are rejected.
    assert client.post(assign_url, json={"delivery_person_id": courier_id}).status_code == 401
    assert (
        client.post(
            assign_url, json={"delivery_person_id": courier_id}, headers=customer
        ).status_code
        == 403
    )
    assert (
        client.post(
            assign_url, json={"delivery_person_id": courier_id}, headers=courier
        ).status_code
        == 403
    )

    # Pending order (not yet accepted) cannot be assigned.
    not_accepted = client.post(
        assign_url, json={"delivery_person_id": courier_id}, headers=restaurant_manager
    )
    assert (
        not_accepted.status_code == 409
        and not_accepted.json()["error"]["code"] == "invalid_order_state"
    )

    # Accept the order -> eligible for assignment.
    assert (
        client.patch(
            f"/api/v1/operations/orders/{order['id']}/status",
            json={"status": "accepted"},
            headers=restaurant_manager,
        ).status_code
        == 200
    )

    # Non-existent order or courier -> 404; non-courier user -> 400.
    assert (
        client.post(
            f"/api/v1/orders/{uuid4()}/delivery-assignment",
            json={"delivery_person_id": courier_id},
            headers=restaurant_manager,
        ).status_code
        == 404
    )
    assert (
        client.post(
            assign_url, json={"delivery_person_id": str(uuid4())}, headers=restaurant_manager
        ).status_code
        == 404
    )
    assert (
        client.post(
            assign_url, json={"delivery_person_id": customer_id}, headers=restaurant_manager
        ).status_code
        == 400
    )
    assert (
        client.post(
            assign_url,
            json={"delivery_person_id": courier_id},
            headers=other_restaurant_manager,
        ).status_code
        == 403
    )

    # Valid assignment succeeds with 201 and ASSIGNED status.
    assigned = client.post(
        assign_url, json={"delivery_person_id": courier_id}, headers=restaurant_manager
    )
    assert assigned.status_code == 201, assigned.text
    body = assigned.json()["data"]
    assert body["order_id"] == order["id"]
    assert body["delivery_person_id"] == courier_id
    assert body["assignment_status"] == "ASSIGNED"

    # Duplicate POST assignment fails with 409 delivery_already_assigned.
    dup = client.post(
        assign_url, json={"delivery_person_id": courier_id}, headers=restaurant_manager
    )
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "delivery_already_assigned"

    # Courier directory reflects active assigned order count.
    couriers = client.get("/api/v1/delivery/couriers", headers=restaurant_manager).json()["data"][
        "couriers"
    ]
    matched = next(c for c in couriers if c["id"] == courier_id)
    assert matched["active_order_count"] == 1


def test_reassignment_my_orders_isolation_and_post_pickup_lock(
    client, customer, restaurant_manager, courier, second_courier, address
):
    order = create_cash_order(client, customer, address)
    assign_url = f"/api/v1/orders/{order['id']}/delivery-assignment"
    c1_id = user_id(client, courier)
    c2_id = user_id(client, second_courier)

    advance_to_ready(client, restaurant_manager, order["id"])

    # Reassignment before initial assignment -> 409.
    before_assign = client.patch(
        assign_url, json={"new_delivery_person_id": c2_id}, headers=restaurant_manager
    )
    assert (
        before_assign.status_code == 409
        and before_assign.json()["error"]["code"] == "delivery_not_assigned"
    )

    assert (
        client.post(
            assign_url, json={"delivery_person_id": c1_id}, headers=restaurant_manager
        ).status_code
        == 201
    )

    # Same courier reassignment -> 409.
    same = client.patch(
        assign_url, json={"new_delivery_person_id": c1_id}, headers=restaurant_manager
    )
    assert same.status_code == 409 and same.json()["error"]["code"] == "same_delivery_person"

    # Reassign from courier 1 to courier 2 -> 200 REASSIGNED.
    reassigned = client.patch(
        assign_url, json={"new_delivery_person_id": c2_id}, headers=restaurant_manager
    )
    assert reassigned.status_code == 200, reassigned.text
    rdata = reassigned.json()["data"]
    assert rdata["previous_delivery_person_id"] == c1_id
    assert rdata["new_delivery_person_id"] == c2_id
    assert rdata["assignment_status"] == "REASSIGNED"

    # Old courier loses visibility; new courier sees it in my-orders.
    assert client.get("/api/v1/delivery/my-orders", headers=courier).json()["data"]["orders"] == []
    c2_orders = client.get("/api/v1/delivery/my-orders", headers=second_courier).json()["data"][
        "orders"
    ]
    assert [o["id"] for o in c2_orders] == [order["id"]]
    assert c2_orders[0]["delivery_assignment"]["status"] == "REASSIGNED"

    # Old courier (and customer/manager) cannot update pickup status.
    del_status_url = f"/api/v1/delivery/orders/{order['id']}/status"
    assert (
        client.patch(del_status_url, json={"status": "PICKED_UP"}, headers=courier).status_code
        == 403
    )
    assert (
        client.patch(del_status_url, json={"status": "PICKED_UP"}, headers=customer).status_code
        == 403
    )
    assert (
        client.patch(
            del_status_url, json={"status": "PICKED_UP"}, headers=restaurant_manager
        ).status_code
        == 403
    )

    # Assigned courier picks up -> cannot jump straight to delivered before pickup, can deliver after.
    picked = client.patch(del_status_url, json={"status": "PICKED_UP"}, headers=second_courier)
    assert picked.status_code == 200
    assert picked.json()["data"]["previous_status"] == "ready_for_pickup"
    assert picked.json()["data"]["current_status"] == "picked_up"

    # Reassignment after pickup is blocked -> 409 reassignment_not_allowed.
    after_pickup = client.patch(
        assign_url, json={"new_delivery_person_id": c1_id}, headers=restaurant_manager
    )
    assert (
        after_pickup.status_code == 409
        and after_pickup.json()["error"]["code"] == "reassignment_not_allowed"
    )

    # Courier completes delivery -> COD settles to paid.
    delivered = client.patch(del_status_url, json={"status": "DELIVERED"}, headers=second_courier)
    assert delivered.status_code == 200
    assert delivered.json()["data"]["current_status"] == "delivered"
    assert delivered.json()["data"]["order"]["payment_status"] == "paid"


def test_courier_cannot_pickup_before_ready_or_bypass_transitions(
    client, customer, restaurant_manager, courier, address
):
    order = create_cash_order(client, customer, address)
    c1_id = user_id(client, courier)

    assert (
        client.patch(
            f"/api/v1/orders/{order['id']}/delivery-assignment"
        ).status_code
        == 401
    )
    client.patch(
        f"/api/v1/operations/orders/{order['id']}/status",
        json={"status": "accepted"},
        headers=restaurant_manager,
    )
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/delivery-assignment",
            json={"delivery_person_id": c1_id},
            headers=restaurant_manager,
        ).status_code
        == 201
    )

    del_url = f"/api/v1/delivery/orders/{order['id']}/status"
    assert client.patch(del_url, json={"status": "PICKED_UP"}, headers=courier).status_code == 409
    assert client.patch(del_url, json={"status": "DELIVERED"}, headers=courier).status_code == 409
    assert client.patch(del_url, json={"status": "accepted"}, headers=courier).status_code == 422


def test_order_cancellation_rules_before_and_after_acceptance(
    client, customer, restaurant_manager, other_restaurant_manager, courier, address
):
    order1 = create_cash_order(client, customer, address)
    stranger = auth_header(register_and_login(client, email="stranger-cancel@example.com"))

    # Courier, stranger, and other restaurant's manager cannot cancel.
    assert client.post(f"/api/v1/orders/{order1['id']}/cancel", headers=courier).status_code == 403
    assert client.post(f"/api/v1/orders/{order1['id']}/cancel", headers=stranger).status_code == 403
    assert (
        client.post(
            f"/api/v1/orders/{order1['id']}/cancel", headers=other_restaurant_manager
        ).status_code
        == 403
    )

    # Customer can cancel while pending.
    cancelled = client.post(
        f"/api/v1/orders/{order1['id']}/cancel",
        json={"note": "Changed mind"},
        headers=customer,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["order"]["status"] == "cancelled"

    # Once accepted, cancellation is rejected with 409.
    order2 = create_cash_order(client, customer, address)
    assert (
        client.patch(
            f"/api/v1/operations/orders/{order2['id']}/status",
            json={"status": "accepted"},
            headers=restaurant_manager,
        ).status_code
        == 200
    )
    blocked = client.post(f"/api/v1/orders/{order2['id']}/cancel", headers=customer)
    assert blocked.status_code == 409 and blocked.json()["error"]["code"] == "order_cannot_be_cancelled"

    # Non-existent order -> 404.
    assert client.post(f"/api/v1/orders/{uuid4()}/cancel", headers=customer).status_code == 404
