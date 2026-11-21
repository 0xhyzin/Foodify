"""Catalog reads, filters, pagination and authenticated favorite bridges."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.ordering.models import Restaurant

REST = "11111111-1111-4111-8111-111111111111"
MARKET = "22222222-2222-4222-8222-222222222222"


pytestmark = pytest.mark.integration


def test_list_returns_database_catalog(client):
    body = client.get("/api/v1/restaurants").json()["data"]
    assert len(body["restaurants"]) == 2
    assert body["pagination"] == {"limit": 20, "offset": 0, "has_more": False}
    assert set(body["restaurants"][0]) >= {"id", "name", "rating", "delivery_fee", "artwork", "kind", "tags"}


@pytest.mark.parametrize("query,expected", [
    ("category=burgers", [REST]), ("search=BURGER", [REST]),
    ("search=milk", [MARKET]), ("kind=grocery", [MARKET]),
    ("free_delivery=true", [MARKET]), ("max_delivery_minutes=25", [MARKET]),
    ("category=unknown", []), ("search=unmatched", []),
    ("category=burgers&search=milk", []),
])
def test_catalog_filters(client, query, expected):
    response = client.get("/api/v1/restaurants?" + query)
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()["data"]["restaurants"]] == expected


def test_sort_and_pagination(client):
    first = client.get("/api/v1/restaurants?sort=fastest&limit=1").json()["data"]
    second = client.get("/api/v1/restaurants?sort=fastest&limit=1&offset=1").json()["data"]
    assert first["restaurants"][0]["id"] == MARKET
    assert first["pagination"]["has_more"] is True
    assert second["restaurants"][0]["id"] == REST
    assert second["pagination"]["has_more"] is False


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "sort=arbitrary", "kind=invalid"])
def test_unbounded_or_unknown_query_rejected(client, query):
    assert client.get("/api/v1/restaurants?" + query).status_code == 422


def test_details_and_menu_categories(client):
    response = client.get(f"/api/v1/restaurants/{REST}")
    assert response.status_code == 200
    assert set(response.json()["data"]["restaurant"]["categories"]) == {"Burgers", "Sides"}
    assert client.get(f"/api/v1/restaurants/{REST}/categories").json()["data"]["categories"]


@pytest.mark.parametrize("suffix", ["", "/menu", "/categories"])
def test_unknown_restaurant_returns_404(client, suffix):
    assert client.get(f"/api/v1/restaurants/{uuid4()}{suffix}").status_code == 404


def test_menu_fields_and_category_filter(client):
    response = client.get(f"/api/v1/restaurants/{REST}/menu?category=Burgers")
    items = response.json()["data"]["menu"]
    assert len(items) == 1
    assert items[0]["name"] == "Cheese Burger"
    assert items[0]["price"] == "45.25"


def test_inactive_restaurant_hidden(client, db):
    db.get(Restaurant, REST).is_active = False
    db.commit()
    assert len(client.get("/api/v1/restaurants").json()["data"]["restaurants"]) == 1
    assert client.get(f"/api/v1/restaurants/{REST}").status_code == 404


def test_favorite_is_idempotent_and_user_owned(client, customer):
    endpoint = f"/api/v1/users/me/favorites/{REST}"
    assert client.put(endpoint, json={"favorite": True}, headers=customer).status_code == 200
    repeated = client.put(endpoint, json={"favorite": True}, headers=customer)
    assert repeated.status_code == 200
    assert client.get("/api/v1/users/me/favorites", headers=customer).json()["data"]["restaurant_ids"] == [REST]
    assert client.put(endpoint, json={"favorite": False}, headers=customer).status_code == 200
    assert client.get("/api/v1/users/me/favorites", headers=customer).json()["data"]["restaurant_ids"] == []
