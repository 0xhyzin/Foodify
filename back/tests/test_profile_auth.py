"""Own-profile/address contracts and operations authorization."""

from uuid import uuid4

import pytest

from conftest import ADDRESS, auth_header, register_and_login


pytestmark = pytest.mark.integration


def test_get_current_profile(client, customer):
    response = client.get("/api/v1/users/me", headers=customer)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["roles"] == ["customer"]


def test_update_profile_name_and_phone(client, customer):
    response = client.patch("/api/v1/users/me", json={"name": "New Name", "phone": "+201001234567"}, headers=customer)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "New Name"
    assert response.json()["phone"] == "+201001234567"


@pytest.mark.parametrize("payload", [{}, {"name": None}, {"name": " "}, {"phone": "bad"}, {"email": "new@example.com"}, {"roles": ["admin"]}])
def test_profile_rejects_invalid_or_privileged_fields(client, customer, payload):
    assert client.patch("/api/v1/users/me", json=payload, headers=customer).status_code == 422


def test_first_address_becomes_default_and_completes_profile(client, customer, address):
    client.patch("/api/v1/users/me", json={"phone": ADDRESS["phone"]}, headers=customer)
    body = client.get("/api/v1/users/me", headers=customer).json()
    assert body["default_address_id"] == address
    assert body["profile_complete"] is True
    assert client.get("/api/v1/users/me/addresses", headers=customer).json()[0]["is_default"] is True


def test_address_ownership_cannot_be_changed_or_read_by_other_customer(client, customer, address):
    other = auth_header(register_and_login(client, email="other@example.com"))
    assert client.get("/api/v1/users/me/addresses", headers=other).json() == []
    assert client.put(f"/api/v1/users/me/addresses/{address}", json=ADDRESS, headers=other).status_code == 404
    assert client.delete(f"/api/v1/users/me/addresses/{address}", headers=other).status_code == 404
    assert client.put(f"/api/v1/users/me/default-address/{address}", headers=other).status_code == 404


def test_update_and_delete_owned_address(client, customer, address):
    response = client.put(f"/api/v1/users/me/addresses/{address}", json={**ADDRESS, "street": "Updated Street"}, headers=customer)
    assert response.status_code == 200 and response.json()["street"] == "Updated Street"
    assert client.delete(f"/api/v1/users/me/addresses/{address}", headers=customer).status_code == 204
    assert client.get("/api/v1/users/me", headers=customer).json()["default_address_id"] is None


@pytest.mark.parametrize("change", [{"latitude": "30.1"}, {"longitude": "31.1"}, {"latitude": "91", "longitude": "31"}])
def test_invalid_coordinates_rejected(client, customer, change):
    assert client.post("/api/v1/users/me/addresses", json={**ADDRESS, **change}, headers=customer).status_code == 422


def test_customer_cannot_read_operational_restaurant_orders(client, customer):
    assert client.get("/api/v1/restaurant/orders?restaurant_id=11111111-1111-4111-8111-111111111111", headers=customer).status_code == 403


def test_customer_cannot_update_operational_order_status(client, customer):
    response = client.patch(f"/api/v1/operations/orders/{uuid4()}/status", json={"status": "preparing"}, headers=customer)
    assert response.status_code == 403


def test_operator_can_read_restaurant_order_list(client, operator):
    response = client.get("/api/v1/restaurant/orders?restaurant_id=11111111-1111-4111-8111-111111111111", headers=operator)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["orders"] == []
