"""Cart/checkout/order integration against a fresh isolated SQL database per test."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.ordering.models import FoodOrder, MenuItem
from conftest import ADDRESS, auth_header, register_and_login
from test_restaurants import MARKET, REST

BURGER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
MILK = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def add_item(client, headers, restaurant=REST, item=BURGER, quantity=2):
    return client.post(f"/api/v1/carts/{restaurant}/items", json={"menu_item_id": item, "quantity": quantity}, headers=headers)


def checkout(client, headers, address, *, method="cash", key=None, cart=None, **changes):
    if cart is None:
        cart = client.get(f"/api/v1/carts/{REST}", headers=headers).json()["data"]["cart"]
    payload = {"restaurant_id": REST, "address_id": address, "payment_method": method,
               "expected_total": cart["total"], "cart_revision": cart["revision"], **changes}
    return client.post("/api/v1/checkout", json=payload, headers={**headers, "Idempotency-Key": key or str(uuid4())})


pytestmark = pytest.mark.integration


def test_cart_quantities_totals_and_independent_restaurants(client, customer):
    first = add_item(client, customer).json()["data"]["cart"]
    assert first["subtotal"] == "90.50" and first["total"] == "100.50"
    assert add_item(client, customer, MARKET, MILK, 1).status_code == 201
    carts = client.get("/api/v1/carts", headers=customer).json()["data"]["carts"]
    assert len(carts) == 2
    updated = client.patch(f"/api/v1/carts/{REST}/items/{first['items'][0]['id']}", json={"quantity": 3}, headers=customer)
    assert updated.json()["data"]["cart"]["total"] == "145.75"
    assert updated.json()["data"]["cart"]["revision"] > first["revision"]
    assert client.delete(f"/api/v1/carts/{REST}", headers=customer).status_code == 200
    assert client.get(f"/api/v1/carts/{MARKET}", headers=customer).json()["data"]["cart"]["total"] == "25.00"


def test_repeated_add_coalesces_one_line(client, customer):
    add_item(client, customer, quantity=1)
    cart = add_item(client, customer, quantity=2).json()["data"]["cart"]
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 3


@pytest.mark.parametrize("quantity", [0, -1, 100, True, 1.5, "2"])
def test_cart_quantity_bounds_and_strict_type(client, customer, quantity):
    assert add_item(client, customer, quantity=quantity).status_code == 422


def test_cart_cannot_exceed_quantity_limit_by_repeated_add(client, customer):
    assert add_item(client, customer, quantity=99).status_code == 201
    response = add_item(client, customer, quantity=1)
    assert response.status_code == 409 and response.json()["error"]["code"] == "quantity_limit_exceeded"


def test_item_from_another_restaurant_cannot_enter_cart(client, customer):
    assert add_item(client, customer, REST, MILK).status_code == 404


def test_other_account_cannot_mutate_or_observe_customer_cart(client, customer):
    cart = add_item(client, customer).json()["data"]["cart"]
    other = auth_header(register_and_login(client, email="other@example.com"))
    assert client.get(f"/api/v1/carts/{REST}", headers=other).json()["data"]["cart"]["items"] == []
    response = client.patch(f"/api/v1/carts/{REST}/items/{cart['items'][0]['id']}", json={"quantity": 1}, headers=other)
    assert response.status_code == 404


def test_remove_item_preserves_other_lines(client, customer):
    cart = add_item(client, customer).json()["data"]["cart"]
    assert client.delete(f"/api/v1/carts/{REST}/items/{cart['items'][0]['id']}", headers=customer).status_code == 200
    assert client.get(f"/api/v1/carts/{REST}", headers=customer).json()["data"]["cart"]["total"] == "0.00"


def test_cash_checkout_snapshots_data_and_clears_only_its_cart(client, customer, address, db):
    add_item(client, customer)
    add_item(client, customer, MARKET, MILK, 1)
    response = checkout(client, customer, address)
    assert response.status_code == 201, response.text
    order = response.json()["data"]["order"]
    assert order["status"] == "pending" and order["payment_status"] == "due_on_delivery"
    assert order["total"] == "100.50" and order["delivery_address"]["street"] == ADDRESS["street"]
    assert client.get(f"/api/v1/carts/{REST}", headers=customer).json()["data"]["cart"]["items"] == []
    assert client.get(f"/api/v1/carts/{MARKET}", headers=customer).json()["data"]["cart"]["items"]
    item = db.get(MenuItem, BURGER)
    item.name, item.price = "New menu name", 500
    db.commit()
    client.put(f"/api/v1/users/me/addresses/{address}", json={**ADDRESS, "street": "New street"}, headers=customer)
    saved = client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]
    assert saved["items"][0]["name"] == "Cheese Burger" and saved["items"][0]["unit_price"] == "45.25"
    assert saved["delivery_address"]["street"] == ADDRESS["street"]


def test_checkout_replay_returns_one_order_even_after_cart_cleared(client, customer, address, db):
    cart = add_item(client, customer).json()["data"]["cart"]
    key = str(uuid4())
    original = checkout(client, customer, address, key=key, cart=cart)
    replay = checkout(client, customer, address, key=key, cart=cart)
    assert original.status_code == replay.status_code == 201
    assert replay.json()["data"]["is_replay"] is True
    assert replay.json()["data"]["order"]["id"] == original.json()["data"]["order"]["id"]
    assert db.scalar(select(func.count()).select_from(FoodOrder)) == 1


def test_idempotency_key_reuse_for_changed_payload_rejected(client, customer, address):
    cart = add_item(client, customer).json()["data"]["cart"]
    key = str(uuid4())
    assert checkout(client, customer, address, key=key, cart=cart).status_code == 201
    response = checkout(client, customer, address, key=key, cart=cart, expected_total="111.00")
    assert response.status_code == 409 and response.json()["error"]["code"] == "idempotency_key_reused"


def test_checkout_stale_cart_revision_rejected(client, customer, address):
    cart = add_item(client, customer).json()["data"]["cart"]
    add_item(client, customer, quantity=1)
    response = checkout(client, customer, address, cart=cart)
    assert response.status_code == 409 and response.json()["error"]["code"] == "cart_changed"


def test_checkout_cannot_trust_client_total(client, customer, address, db):
    add_item(client, customer)
    response = checkout(client, customer, address, expected_total="1.00")
    assert response.status_code == 409 and response.json()["error"]["code"] == "cart_price_changed"
    assert db.scalar(select(func.count()).select_from(FoodOrder)) == 0


def test_checkout_rejects_price_change_after_review(client, customer, address, db):
    cart = add_item(client, customer).json()["data"]["cart"]
    db.get(MenuItem, BURGER).price = 50
    db.commit()
    assert checkout(client, customer, address, cart=cart).json()["error"]["code"] == "cart_price_changed"


def test_checkout_rejects_unavailable_item(client, customer, address, db):
    add_item(client, customer)
    db.get(MenuItem, BURGER).is_available = False
    db.commit()
    response = checkout(client, customer, address)
    assert response.status_code == 409 and response.json()["error"]["code"] == "menu_item_unavailable"


def test_checkout_rejects_other_customers_address(client, customer, address):
    other = auth_header(register_and_login(client, email="other@example.com"))
    add_item(client, other)
    assert checkout(client, other, address).status_code == 404


def test_online_checkout_preserves_cart_until_verified_payment(client, customer, address):
    add_item(client, customer)
    order = checkout(client, customer, address, method="card").json()["data"]["order"]
    assert order["status"] == "awaiting_payment" and order["payment_status"] == "pending"
    assert client.get(f"/api/v1/carts/{REST}", headers=customer).json()["data"]["cart"]["items"]


def test_orders_history_and_details_are_owned(client, customer, address):
    add_item(client, customer)
    order = checkout(client, customer, address).json()["data"]["order"]
    other = auth_header(register_and_login(client, email="other@example.com"))
    assert client.get(f"/api/v1/orders/{order['id']}", headers=other).status_code == 404
    assert client.get("/api/v1/orders", headers=other).json()["data"]["orders"] == []
    assert client.get("/api/v1/orders", headers=customer).json()["data"]["orders"][0]["id"] == order["id"]


def test_operations_enforces_sequential_tracking_and_records_cash_settlement(
    client, customer, operator, courier, address
):
    add_item(client, customer)
    order = checkout(client, customer, address).json()["data"]["order"]
    op_endpoint = f"/api/v1/operations/orders/{order['id']}/status"
    assert client.patch(op_endpoint, json={"status": "ready_for_pickup"}, headers=operator).status_code == 409
    assert client.patch(op_endpoint, json={"status": "delivered"}, headers=operator).status_code == 403

    for status in ("accepted", "preparing", "ready_for_pickup"):
        response = client.patch(op_endpoint, json={"status": status}, headers=operator)
        assert response.status_code == 200, response.text

    courier_id = client.get("/api/v1/users/me", headers=courier).json()["id"]
    assigned = client.post(
        f"/api/v1/orders/{order['id']}/delivery-assignment",
        json={"delivery_person_id": courier_id},
        headers=operator,
    )
    assert assigned.status_code == 201, assigned.text

    del_endpoint = f"/api/v1/delivery/orders/{order['id']}/status"
    for status in ("PICKED_UP", "DELIVERED"):
        response = client.patch(del_endpoint, json={"status": status}, headers=courier)
        assert response.status_code == 200, response.text

    order = response.json()["data"]["order"]
    assert order["payment_status"] == "paid"
    assert [entry["status"] for entry in order["events"]] == [
        "pending",
        "accepted",
        "preparing",
        "ready_for_pickup",
        "ready_for_pickup",
        "picked_up",
        "delivered",
    ]


def test_unpaid_online_order_cannot_start_fulfillment(client, customer, operator, address):
    add_item(client, customer)
    order = checkout(client, customer, address, method="card").json()["data"]["order"]
    response = client.patch(
        f"/api/v1/operations/orders/{order['id']}/status",
        json={"status": "accepted"},
        headers=operator,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payment_not_confirmed"
