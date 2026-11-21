"""Current FastAPI registration, confirmation, session and password contracts."""

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.infrastructure.models import ActionToken, AuthSession, EmailOutbox, User
from app.shared.time import utcnow
from conftest import (
    BROWSER_HEADERS, PASSWORD, action_token, auth_header, login, register,
    register_and_login, verify_registered,
)


pytestmark = pytest.mark.integration


def test_registration_is_generic_and_does_not_issue_session(client, db):
    response = register(client)
    assert response.status_code == 202
    assert set(response.json()) == {"message"}
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert db.scalar(select(func.count()).select_from(EmailOutbox)) == 1
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_duplicate_registration_is_indistinguishable_and_creates_no_duplicate(client, db):
    original = register(client)
    repeated = register(client)
    assert (repeated.status_code, repeated.json()) == (original.status_code, original.json())
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert db.scalar(select(func.count()).select_from(EmailOutbox)) == 1


def test_email_normalization_and_customer_role(client, db):
    register(client, email="MiXeD@Example.COM ")
    user = db.scalar(select(User))
    assert user.email == "mixed@example.com"
    assert [role.code for role in user.roles] == ["customer"]


@pytest.mark.parametrize("payload", [
    {}, {"name": "Test", "email": "bad", "password": PASSWORD},
    {"name": "   ", "email": "test@example.com", "password": PASSWORD},
    {"name": "Test", "email": "test@example.com", "password": "short"},
    {"name": "Test", "email": "test@example.com"},
    {"name": "Test", "email": "test@example.com", "password": PASSWORD, "roles": ["admin"]},
])
def test_invalid_registration_is_rejected(client, payload):
    assert client.post("/api/v1/auth/register", json=payload).status_code == 422


def test_malformed_json_is_rejected_without_input_echo(client):
    response = client.post("/api/v1/auth/register", content="not-json-secret", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert "not-json-secret" not in response.text


def test_unverified_customer_cannot_password_login(client):
    register(client)
    response = login(client)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "email_verification_required"


def test_browser_confirmation_issues_session_and_does_not_expose_refresh_token(client, db):
    register(client)
    raw = action_token(db)
    response = client.post("/api/v1/auth/browser/verify-email", json={"token": raw}, headers=BROWSER_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["email_verified"] is True
    assert body["user"]["profile_complete"] is False
    assert "refresh_token" not in body
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    assert client.get("/api/v1/users/me", headers=auth_header(body["access_token"])).status_code == 200
    assert client.post("/api/v1/auth/browser/verify-email", json={"token": raw}, headers=BROWSER_HEADERS).status_code == 400


@pytest.mark.parametrize("headers", [{}, {"Origin": "https://evil.example", "X-Foodify-Client": "web"}, {"Origin": "http://127.0.0.1:5173"}])
def test_browser_confirmation_requires_origin_and_client_header(client, db, headers):
    register(client)
    response = client.post("/api/v1/auth/browser/verify-email", json={"token": action_token(db)}, headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize("minutes,consumed", [(-1, False), (10, True)])
def test_expired_or_used_proof_cannot_create_session(client, db, minutes, consumed):
    register(client)
    raw = action_token(db, minutes=minutes, consumed=consumed)
    assert client.post("/api/v1/auth/browser/verify-email", json={"token": raw}, headers=BROWSER_HEADERS).status_code == 400
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_legacy_confirmation_confirms_without_creating_session(client, db):
    register(client)
    response = client.post("/api/v1/auth/verify-email", json={"token": action_token(db)})
    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 0
    assert login(client).status_code == 200


def test_confirmation_rolls_back_when_session_issuance_fails(client, db, monkeypatch):
    register(client)
    raw = action_token(db)
    from app.users.shared.session_issuer import SessionIssuer
    create_session = SessionIssuer.create_session

    def fail(*args):
        raise RuntimeError("isolated session failure")

    monkeypatch.setattr(SessionIssuer, "create_session", fail)
    from fastapi.testclient import TestClient
    safe_client = TestClient(client.app, raise_server_exceptions=False)
    response = safe_client.post("/api/v1/auth/browser/verify-email", json={"token": raw}, headers=BROWSER_HEADERS)
    safe_client.close()
    assert response.status_code == 500
    db.expire_all()
    assert db.scalar(select(User)).is_email_verified is False
    assert db.scalar(select(ActionToken)).consumed_at is None
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 0
    monkeypatch.setattr(SessionIssuer, "create_session", create_session)
    retry = client.post("/api/v1/auth/browser/verify-email", json={"token": raw}, headers=BROWSER_HEADERS)
    assert retry.status_code == 200, retry.text


def test_valid_login_issues_bound_jwt_without_password(client, settings):
    token = register_and_login(client)
    import jwt
    claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience=settings.jwt_audience, issuer=settings.jwt_issuer)
    assert claims["type"] == "access" and claims["sid"] and claims["sub"]
    assert "role" not in claims
    profile = client.get("/api/v1/users/me", headers=auth_header(token))
    assert PASSWORD not in profile.text and "password_hash" not in profile.text


def test_wrong_credentials_share_generic_error(client):
    register(client)
    wrong = login(client, password="Incorrect long password")
    missing = login(client, email="absent@example.com")
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json()["error"]["message"] == missing.json()["error"]["message"]


def test_logout_revokes_current_access(client):
    token = register_and_login(client)
    assert client.post("/api/v1/auth/logout", headers=auth_header(token)).status_code == 204
    assert client.get("/api/v1/users/me", headers=auth_header(token)).status_code == 401


def test_browser_refresh_rotates_cookie_and_revokes_reuse(client):
    register(client)
    verify_registered(client)
    response = client.post("/api/v1/auth/browser/login", json={"email": "test@example.com", "password": PASSWORD}, headers=BROWSER_HEADERS)
    assert response.status_code == 200, response.text
    old_cookie = next(iter(client.cookies.values()))
    response = client.post("/api/v1/auth/browser/refresh", headers=BROWSER_HEADERS)
    assert response.status_code == 200, response.text
    assert "refresh_token" not in response.json()
    assert old_cookie not in client.cookies.values()


def test_reusing_rotated_refresh_token_revokes_the_whole_session(client):
    register(client)
    verify_registered(client)
    original = login(client).json()
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert rotated.status_code == 200
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert replay.status_code == 401
    assert client.get("/api/v1/users/me", headers=auth_header(rotated.json()["access_token"])).status_code == 401


def test_forgot_password_is_generic(client, db):
    register(client)
    known = client.post("/api/v1/auth/forgot-password", json={"email": "test@example.com"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()


def test_reset_password_revokes_existing_session(client, db):
    token = register_and_login(client)
    client.post("/api/v1/auth/forgot-password", json={"email": "test@example.com"})
    from app.infrastructure.models import TokenType
    proof = db.scalar(select(ActionToken).join(TokenType).where(TokenType.code == "password_reset"))
    from app.shared.tokens import hash_token
    raw = "isolated-password-reset-proof-0123456789"
    proof.token_hash = hash_token(raw)
    proof.expires_at = utcnow() + timedelta(minutes=10)
    db.commit()
    response = client.post("/api/v1/auth/reset-password", json={"token": raw, "password": "An updated secure password 2026!"})
    assert response.status_code == 200, response.text
    assert client.get("/api/v1/users/me", headers=auth_header(token)).status_code == 401
    assert login(client, password="An updated secure password 2026!").status_code == 200
