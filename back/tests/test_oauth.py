"""Provider identity is mocked; browser-bound tickets and sessions are real."""

import hashlib
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import func, select

from app.infrastructure.models import OAuthState, SocialAccount, User
from app.infrastructure.oauth import SocialOAuthGateway
from app.shared.ports import OAuthIdentity
from conftest import BROWSER_HEADERS, auth_header, register

VERIFIER = "isolated-browser-binding-verifier-0123456789abcdef"

pytestmark = pytest.mark.integration


def begin(client):
    challenge = hashlib.sha256(VERIFIER.encode()).hexdigest()
    response = client.post("/api/v1/auth/oauth/google/start", json={"binding_challenge": challenge})
    assert response.status_code == 200, response.text
    params = parse_qs(urlsplit(response.json()["authorization_url"]).query)
    assert params["redirect_uri"] == ["http://localhost:8000/api/v1/auth/oauth/google/callback"]
    return params["state"][0]


def callback(client, state):
    return client.get("/api/v1/auth/oauth/google/callback", params={"state": state, "code": "mock-provider-code"}, follow_redirects=False)


def provider(monkeypatch, *, verified=True, email="newgoogle@gmail.com"):
    identity = OAuthIdentity("google", "google-subject-42", email, verified, "Google Customer")
    monkeypatch.setattr(SocialOAuthGateway, "exchange_identity", lambda *args: identity)


def test_google_new_customer_receives_session_with_incomplete_profile(client, db, monkeypatch):
    provider(monkeypatch)
    state = begin(client)
    response = callback(client, state)
    assert response.status_code == 303
    assert response.headers["location"].startswith("http://127.0.0.1:5173/oauth/callback#")
    ticket = parse_qs(urlsplit(response.headers["location"]).fragment)["ticket"][0]
    completed = client.post("/api/v1/auth/browser/oauth/complete", json={"ticket": ticket, "binding_verifier": VERIFIER}, headers=BROWSER_HEADERS)
    assert completed.status_code == 200, completed.text
    body = completed.json()
    assert body["user"]["name"] == "Google Customer"
    assert body["user"]["phone"] is None and body["user"]["default_address_id"] is None
    assert body["user"]["profile_complete"] is False and "refresh_token" not in body
    assert "httponly" in completed.headers["set-cookie"].lower()
    assert db.scalar(select(User)).password_hash is None
    assert db.scalar(select(func.count()).select_from(SocialAccount)) == 1
    assert client.get("/api/v1/users/me", headers=auth_header(body["access_token"])).status_code == 200
    assert client.post("/api/v1/auth/browser/oauth/complete", json={"ticket": ticket, "binding_verifier": VERIFIER}, headers=BROWSER_HEADERS).status_code == 400


def test_google_email_match_does_not_silently_link_existing_password_account(client, db, monkeypatch):
    register(client, email="newgoogle@gmail.com")
    provider(monkeypatch)
    response = callback(client, begin(client))
    assert urlsplit(response.headers["location"]).fragment == "error=oauth_account_link_required"
    assert db.scalar(select(func.count()).select_from(SocialAccount)) == 0


def test_wrong_browser_binding_cannot_exchange_google_ticket(client, monkeypatch):
    provider(monkeypatch)
    response = callback(client, begin(client))
    ticket = parse_qs(urlsplit(response.headers["location"]).fragment)["ticket"][0]
    completed = client.post("/api/v1/auth/browser/oauth/complete", json={"ticket": ticket, "binding_verifier": "another-browser-binding-verifier-0123456789abcdef"}, headers=BROWSER_HEADERS)
    assert completed.status_code == 400 and completed.json()["error"]["code"] == "invalid_oauth_ticket"
    # A thief's incorrect verifier must not consume the legitimate browser's ticket.
    recovered = client.post("/api/v1/auth/browser/oauth/complete", json={"ticket": ticket, "binding_verifier": VERIFIER}, headers=BROWSER_HEADERS)
    assert recovered.status_code == 200


def test_unverified_provider_email_requires_email_proof(client, db, monkeypatch):
    provider(monkeypatch, verified=False)
    response = callback(client, begin(client))
    assert urlsplit(response.headers["location"]).fragment == "error=email_verification_required"
    assert db.scalar(select(User)).is_email_verified is False


def test_replayed_oauth_state_is_rejected(client, monkeypatch):
    provider(monkeypatch)
    state = begin(client)
    assert "ticket=" in callback(client, state).headers["location"]
    assert urlsplit(callback(client, state).headers["location"]).fragment == "error=invalid_oauth_state"


def test_unconfigured_provider_has_no_authorization_url(client):
    response = client.post("/api/v1/auth/oauth/facebook/start", json={"binding_challenge": "0" * 64})
    assert response.status_code == 503
