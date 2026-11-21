"""Isolated FastAPI fixtures: no environment files, external network, or real DB.

SQLite exercises DTOs, HTTP contracts, services and SQLAlchemy repositories.
It does not emulate MySQL row locks, migration DDL or concurrent transactions.
"""

import os
import socket
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings, get_settings
from app.infrastructure.database import Base, get_db
from app.infrastructure.models import ActionToken, Role, User
from app.main import create_app
from app.ordering.models import BrowseCategory, MenuItem, Restaurant, RestaurantStaff
from app.shared.time import utcnow
from app.shared.tokens import hash_token
from app.users.shared.dependencies import resources
from scripts.seed import seed_reference_data

PASSWORD = "A secure test password 2026!"
BROWSER_HEADERS = {"Origin": "http://127.0.0.1:5173", "X-Foodify-Client": "web"}
ADDRESS = {
    "label": "Home", "recipient_name": "Test Customer", "phone": "+201001234567",
    "country_code": "EG", "city": "Cairo", "area": "Nasr City", "street": "Test Street",
    "building": "12", "floor": "3", "apartment": "8", "delivery_notes": "Ring the bell",
}


def pytest_collection_modifyitems(items):
    """Make separate test commands exhaustive and mutually exclusive."""
    for item in items:
        groups = [name for name in ("unit", "integration") if item.get_closest_marker(name)]
        if len(groups) != 1:
            raise pytest.UsageError(f"{item.nodeid} must have exactly one unit/integration marker.")


@pytest.fixture(autouse=True)
def deny_external_network(monkeypatch):
    """All test groups fail immediately if an adapter attempts a socket connection."""
    def reject_network(*args, **kwargs):
        raise AssertionError("Tests must not connect to external services.")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket.socket, "connect_ex", reject_network)


class LocalRateLimiter:
    """Local substitute; Redis adapter behavior has separate unit coverage."""

    def check(self, scope, key, limit, window_seconds):
        pass

    def close(self):
        pass


@pytest.fixture()
def settings(monkeypatch):
    for key in tuple(os.environ):
        if key.casefold() in Settings.model_fields:
            monkeypatch.delenv(key)
    return Settings(
        _env_file=None, app_env="test", embedded_email_worker=False,
        database_url="mysql+pymysql://test:unused@127.0.0.1:1/foodify_isolated_tests",
        redis_url="redis://127.0.0.1:1/15", jwt_secret="09fEaf90TuVYwB76sxZP1234KLiMnc85",
        email_encryption_key=Fernet.generate_key().decode(),
        frontend_url="http://127.0.0.1:5173", public_base_url="http://127.0.0.1:8000",
        trusted_hosts=["testserver", "localhost", "127.0.0.1"],
        cors_origins=["http://127.0.0.1:5173"], allow_simulated_payments=True,
        paymob_secret_key="egy_sk_test_isolated", paymob_public_key="egy_pk_test_isolated",
        paymob_hmac_secret="isolated-hmac-secret", paymob_card_integration_id=101,
        paymob_wallet_integration_id=102, instapay_recipient="foodify@test",
        instapay_recipient_name="Foodify Test",
        oauth_google_client_id="isolated-google-client",
        oauth_google_client_secret="isolated-google-secret",
        oauth_google_redirect_uri="http://localhost:8000/api/v1/auth/oauth/google/callback",
    )


@pytest.fixture()
def app(monkeypatch, settings):
    def reject_network(*args, **kwargs):
        raise AssertionError("Tests must not connect to external services.")

    limiter = LocalRateLimiter()
    original_limiter = resources.get_rate_limiter
    # Patch every imported reference, including helpers calling factories directly.
    # Settings never loads a .env file here.
    for name, module in tuple(sys.modules.items()):
        if module and (name.startswith("app.") or name.startswith("scripts.")):
            if getattr(module, "get_settings", None) is get_settings:
                monkeypatch.setattr(module, "get_settings", lambda: settings)
            if getattr(module, "get_rate_limiter", None) is original_limiter:
                monkeypatch.setattr(module, "get_rate_limiter", lambda: limiter)
    resources.get_token_codec.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def sqlite_constraints(connection, _):
        connection.create_collation("utf8mb4_bin", lambda left, right: (left > right) - (left < right))
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        seed_reference_data(session)
        food = BrowseCategory(code="burgers", name="Burgers", artwork="burger")
        grocery = BrowseCategory(code="groceries", name="Groceries", artwork="grocery")
        restaurants = [
            Restaurant(id="11111111-1111-4111-8111-111111111111", name="Test Burger", category="burger",
                       address="Cairo", delivery_fee=Decimal("10.00"), rating=Decimal("4.50"),
                       categories=[food], delivery_minutes=30),
            Restaurant(id="22222222-2222-4222-8222-222222222222", name="Test Market", category="grocery",
                       kind="grocery", address="Giza", delivery_fee=Decimal("0.00"),
                       rating=Decimal("4.00"), categories=[grocery], delivery_minutes=20),
        ]
        session.add_all(restaurants)
        session.flush()
        session.add_all([
            MenuItem(id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", restaurant_id=restaurants[0].id,
                     name="Cheese Burger", category="Burgers", price=Decimal("45.25")),
            MenuItem(id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", restaurant_id=restaurants[0].id,
                     name="French Fries", category="Sides", price=Decimal("12.50")),
            MenuItem(id="cccccccc-cccc-4ccc-8ccc-cccccccccccc", restaurant_id=restaurants[1].id,
                     name="Fresh Milk", category="Dairy", price=Decimal("25.00")),
        ])

    def isolated_db():
        with factory() as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise

    import app.infrastructure.database as database
    import app.main as main
    monkeypatch.setattr(database, "create_database_engine", reject_network)
    monkeypatch.setattr(database, "get_engine", lambda: engine)
    monkeypatch.setattr(main, "get_engine", lambda: engine)
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_db] = isolated_db
    application.state.test_factory = factory
    application.state.test_settings = settings
    yield application
    resources.get_token_codec.cache_clear()
    engine.dispose()


@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def db(app):
    with app.state.test_factory() as session:
        yield session


def register(client, name="Test User", email="test@example.com", password=PASSWORD, **extra):
    return client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": password, **extra})


def login(client, email="test@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def verify_registered(client, email="test@example.com"):
    with client.app.state.test_factory.begin() as session:
        user = session.scalar(select(User).where(User.email == email))
        user.is_email_verified = True


def register_and_login(client, **kwargs):
    response = register(client, **kwargs)
    assert response.status_code == 202, response.text
    verify_registered(client, kwargs.get("email", "test@example.com"))
    response = login(client, email=kwargs.get("email", "test@example.com"), password=kwargs.get("password", PASSWORD))
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def customer(client):
    token = register_and_login(client)
    return auth_header(token)


@pytest.fixture()
def operator(client):
    token = register_and_login(client, email="operator@example.com")
    with client.app.state.test_factory.begin() as session:
        user = session.scalar(select(User).where(User.email == "operator@example.com"))
        user.roles = [session.scalar(select(Role).where(Role.code == "operations_manager"))]
    return auth_header(token)


def assign_role(client, email: str, role_code: str, *, name: str | None = None, restaurant_id: str | None = None):
    token = register_and_login(client, name=name or role_code.replace("_", " ").title(), email=email)
    with client.app.state.test_factory.begin() as session:
        user = session.scalar(select(User).where(User.email == email))
        user.roles = [session.scalar(select(Role).where(Role.code == role_code))]
        user_id = user.id
        if restaurant_id:
            session.add(RestaurantStaff(restaurant_id=restaurant_id, user_id=user.id, created_at=utcnow()))
    return auth_header(token), user_id


@pytest.fixture()
def courier(client):
    headers, _ = assign_role(client, "courier1@example.com", "courier", name="Courier One")
    return headers


@pytest.fixture()
def second_courier(client):
    headers, _ = assign_role(client, "courier2@example.com", "courier", name="Courier Two")
    return headers


@pytest.fixture()
def restaurant_manager(client):
    headers, _ = assign_role(
        client,
        "manager1@example.com",
        "restaurant_manager",
        name="Burger Manager",
        restaurant_id="11111111-1111-4111-8111-111111111111",
    )
    return headers


@pytest.fixture()
def other_restaurant_manager(client):
    headers, _ = assign_role(
        client,
        "manager2@example.com",
        "restaurant_manager",
        name="Market Manager",
        restaurant_id="22222222-2222-4222-8222-222222222222",
    )
    return headers


@pytest.fixture()
def order_preparer(client):
    headers, _ = assign_role(
        client,
        "preparer1@example.com",
        "order_preparer",
        name="Kitchen Preparer One",
        restaurant_id="11111111-1111-4111-8111-111111111111",
    )
    return headers


@pytest.fixture()
def other_preparer(client):
    headers, _ = assign_role(
        client,
        "preparer2@example.com",
        "order_preparer",
        name="Market Preparer Two",
        restaurant_id="22222222-2222-4222-8222-222222222222",
    )
    return headers


@pytest.fixture()
def address(client, customer):
    response = client.post("/api/v1/users/me/addresses", json=ADDRESS, headers=customer)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def action_token(db, email="test@example.com", *, minutes=10, consumed=False):
    user = db.scalar(select(User).where(User.email == email))
    record = db.scalar(select(ActionToken).where(ActionToken.user_id == user.id))
    raw = "isolated-email-proof-0123456789abcdef"
    record.token_hash = hash_token(raw)
    record.expires_at = utcnow() + timedelta(minutes=minutes)
    record.consumed_at = utcnow() if consumed else None
    db.commit()
    return raw
