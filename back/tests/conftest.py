"""Pytest fixtures — in-memory DB per test, seeded like production."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app, db
from app.routes_auth import REVOKED
from app.seed import seed


@pytest.fixture()
def app():
    app = create_app(config={"DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        db.create_all()
        seed()
        yield app
        db.session.remove()
        db.drop_all()
    REVOKED.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, name="Test User", email="test@example.com", password="secret123"):
    return client.post("/api/auth/register", json={"name": name, "email": email, "password": password})


def login(client, email="test@example.com", password="secret123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client, **kwargs):
    register(client, **kwargs)
    res = login(client, email=kwargs.get("email", "test@example.com"), password=kwargs.get("password", "secret123"))
    return res.get_json()["data"]["token"]
