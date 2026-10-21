"""TC-01 Registration (FR-01, FR-07) and TC-02 Login (FR-02, FR-06) + logout (FR-03)."""
from tests.conftest import auth_header, login, register


class TestRegister:
    # ---------- Positive ----------
    def test_register_success_returns_201(self, client):
        res = register(client)
        assert res.status_code == 201

    def test_register_success_returns_user_without_password(self, client):
        body = register(client).get_json()["data"]["user"]
        assert body["name"] == "Test User"
        assert body["email"] == "test@example.com"
        assert body["role"] == "Customer"
        assert "password" not in body and "PasswordHash" not in body

    def test_register_email_is_normalized(self, client):
        body = register(client, email="MiXeD@Example.COM ").get_json()["data"]["user"]
        assert body["email"] == "mixed@example.com"

    def test_register_default_role_is_customer(self, app, client):
        register(client)
        from app.models import User
        with app.app_context():
            user = User.query.filter_by(Email="test@example.com").first()
            assert user.role.RoleName == "Customer"

    # ---------- Negative ----------
    def test_register_duplicate_email_returns_409(self, client):
        register(client, email="dup@example.com")
        res = register(client, name="Another", email="dup@example.com")
        assert res.status_code == 409
        assert res.get_json()["error"]["code"] == "CONFLICT"

    def test_register_missing_all_fields_returns_400_with_details(self, client):
        res = client.post("/api/auth/register", json={})
        assert res.status_code == 400
        details = res.get_json()["error"]["details"]
        assert len(details) == 3  # name, email, password

    def test_register_invalid_email_returns_400(self, client):
        res = register(client, email="not-an-email")
        assert res.status_code == 400

    def test_register_short_password_returns_400(self, client):
        res = register(client, password="123")
        assert res.status_code == 400

    def test_register_missing_password_returns_400(self, client):
        res = client.post("/api/auth/register", json={"name": "A", "email": "a@b.com"})
        assert res.status_code == 400

    def test_register_non_object_body_returns_400(self, client):
        res = client.post("/api/auth/register", data="not json", content_type="application/json")
        assert res.status_code == 400

    def test_register_empty_string_name_returns_400(self, client):
        res = register(client, name="   ")
        assert res.status_code == 400


class TestLogin:
    def setup_method(self):
        pass

    # ---------- Positive ----------
    def test_login_success_returns_200_and_token(self, client):
        register(client)
        res = login(client)
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "token" in data and data["token"]
        assert data["user"]["email"] == "test@example.com"

    def test_login_token_decodes_to_user_id_and_role(self, app, client):
        register(client)
        token = login(client).get_json()["data"]["token"]
        from app.validators import decode_token
        with app.app_context():
            payload = decode_token(token)
        assert payload is not None
        assert payload["role"] == "Customer"
        assert payload["sub"]

    # ---------- Negative (FR-06) ----------
    def test_login_wrong_password_returns_401_generic_message(self, client):
        register(client)
        res = login(client, password="wrong-password")
        assert res.status_code == 401
        assert res.get_json()["error"]["message"] == "البريد الإلكتروني أو كلمة المرور غير صحيحة"

    def test_login_nonexistent_email_returns_same_generic_message(self, client):
        res = login(client, email="ghost@example.com")
        wrong_pw = login(client, password="whatever123")
        assert res.get_json()["error"]["message"] == wrong_pw.get_json()["error"]["message"]

    def test_login_malformed_email_returns_400(self, client):
        res = login(client, email="bad")
        assert res.status_code == 400

    def test_login_missing_password_returns_400(self, client):
        res = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert res.status_code == 400

    def test_login_no_body_returns_400(self, client):
        res = client.post("/api/auth/login", json=None)
        assert res.status_code == 400


class TestLogout:
    def test_logout_invalidates_token(self, client):
        register(client)
        token = login(client).get_json()["data"]["token"]
        res = client.post("/api/auth/logout", headers=auth_header(token))
        assert res.status_code == 200

        profile = client.get("/api/users/me", headers=auth_header(token))
        assert profile.status_code == 401

    def test_logout_without_token_returns_401(self, client):
        res = client.post("/api/auth/logout")
        assert res.status_code == 401

    def test_logout_with_garbage_token_returns_401(self, client):
        res = client.post("/api/auth/logout", headers=auth_header("garbage.token.here"))
        assert res.status_code == 401
