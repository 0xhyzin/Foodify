"""TC-08 Security / validation / error-envelope NFR tests (NFR-01..04)."""
from app.models import User
from tests.conftest import auth_header, register, register_and_login


class TestPasswordSecurity:
    def test_password_stored_hashed_not_plaintext(self, client):
        register(client, password="plain-secret-123")
        user = User.query.filter_by(Email="test@example.com").first()
        assert user.PasswordHash != "plain-secret-123"
        assert "plain-secret-123" not in user.PasswordHash
        assert user.PasswordHash.startswith(("pbkdf2:", "scrypt:"))

    def test_password_never_appears_in_api_responses(self, client):
        register(client, password="super-secret")
        res = client.post("/api/auth/login", json={"email": "test@example.com", "password": "super-secret"})
        assert "super-secret" not in res.get_data(as_text=True)


class TestErrorEnvelope:
    def test_validation_error_envelope_shape(self, client):
        res = client.post("/api/auth/register", json={})
        assert res.status_code == 400
        error = res.get_json()["error"]
        assert set(error.keys()) == {"code", "message", "details"}

    def test_404_envelope_shape(self, client):
        res = client.get("/api/restaurants/9999")
        assert res.status_code == 404
        body = res.get_json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"

    def test_401_envelope_shape(self, client):
        res = client.get("/api/users/me")
        assert res.status_code == 401
        assert res.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_403_envelope_shape(self, client):
        token = register_and_login(client)
        res = client.post("/api/restaurants", json={"name": "x", "address": "y", "phone": "z"},
                          headers=auth_header(token))
        assert res.status_code == 403
        assert res.get_json()["error"]["code"] == "FORBIDDEN"

    def test_unknown_route_returns_error_envelope(self, client):
        res = client.get("/api/does-not-exist")
        assert res.status_code == 404
        assert res.get_json()["success"] is False


class TestTamperedTokens:
    def test_tampered_token_is_rejected(self, client):
        token = register_and_login(client)
        tampered = token[:-4] + "AAAA"
        res = client.get("/api/users/me", headers=auth_header(tampered))
        assert res.status_code == 401

    def test_token_signed_with_wrong_secret_is_rejected(self, client):
        import jwt as pyjwt
        forged = pyjwt.encode({"sub": 1, "role": "Admin"}, "wrong-secret", algorithm="HS256")
        res = client.get("/api/users/me", headers=auth_header(forged))
        assert res.status_code == 401

    def test_expired_token_is_rejected(self, client):
        from datetime import datetime, timedelta, timezone
        import jwt as pyjwt
        from flask import current_app
        token = register_and_login(client)
        with client.application.app_context():
            expired = pyjwt.encode(
                {"sub": 1, "role": "Customer", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
                current_app.config["JWT_SECRET"], algorithm="HS256",
            )
        res = client.get("/api/users/me", headers=auth_header(expired))
        assert res.status_code == 401


class TestHealth:
    def test_health_endpoint(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.get_json()["data"]["status"] == "ok"
