"""TC-03 Profile (FR-04) and TC-06 Authorization (FR-05 / NFR-02)."""
from tests.conftest import auth_header, login, register, register_and_login  # noqa: F401


class TestProfile:
    # ---------- Positive ----------
    def test_get_me_returns_current_user(self, client):
        register(client)
        token = login(client).get_json()["data"]["token"]
        res = client.get("/api/users/me", headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["email"] == "test@example.com"

    def test_update_name_returns_updated_user(self, client):
        token = register_and_login(client)
        res = client.put("/api/users/me", json={"name": "New Name"}, headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["name"] == "New Name"

    def test_update_email_returns_updated_user(self, client):
        token = register_and_login(client)
        res = client.put("/api/users/me", json={"email": "new@example.com"}, headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["email"] == "new@example.com"

    # ---------- Negative ----------
    def test_get_me_without_token_returns_401(self, client):
        res = client.get("/api/users/me")
        assert res.status_code == 401
        assert res.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_get_me_with_malformed_header_returns_401(self, client):
        res = client.get("/api/users/me", headers={"Authorization": "Basic abc"})
        assert res.status_code == 401

    def test_get_me_with_garbage_token_returns_401(self, client):
        res = client.get("/api/users/me", headers=auth_header("abc.def.ghi"))
        assert res.status_code == 401

    def test_update_profile_empty_payload_returns_400(self, client):
        token = register_and_login(client)
        res = client.put("/api/users/me", json={}, headers=auth_header(token))
        assert res.status_code == 400

    def test_update_profile_invalid_email_returns_400(self, client):
        token = register_and_login(client)
        res = client.put("/api/users/me", json={"email": "bad"}, headers=auth_header(token))
        assert res.status_code == 400

    def test_update_profile_to_existing_email_returns_409(self, client):
        register(client, email="taken@example.com")
        token = register_and_login(client, email="other@example.com")
        res = client.put("/api/users/me", json={"email": "taken@example.com"}, headers=auth_header(token))
        assert res.status_code == 409


class TestRoleBasedAuthorization:
    def test_customer_cannot_create_restaurant(self, client):
        token = register_and_login(client)
        res = client.post("/api/restaurants", json={
            "name": "X", "address": "Y", "phone": "01000000000",
        }, headers=auth_header(token))
        assert res.status_code == 403
        assert res.get_json()["error"]["code"] == "FORBIDDEN"

    def test_customer_cannot_delete_menu_item(self, client):
        token = register_and_login(client)
        res = client.delete("/api/restaurants/menu-items/1", headers=auth_header(token))
        assert res.status_code == 403

    def test_manager_can_create_restaurant(self, client, app):
        # Registration always creates a Customer; promote to manager directly
        # (self-promotion via the API must never happen — covered below).
        from app.models import Role, User
        register_and_login(client, email="manager2@example.com", password="secret123")
        with app.app_context():
            user = User.query.filter_by(Email="manager2@example.com").first()
            user.RoleID = Role.query.filter_by(RoleName="RestaurantManager").first().RoleID
            from app import db
            db.session.commit()
            token = __import__("app.validators", fromlist=["generate_token"]).generate_token(user)
        res = client.post("/api/restaurants", json={
            "name": "My Place", "address": "Cairo", "phone": "01000000000",
        }, headers=auth_header(token))
        assert res.status_code == 201

    def test_registration_cannot_self_promote_to_manager(self, client):
        # Security: the public register endpoint must always create Customers.
        res = register(client, email="evil@example.com", password="secret123")
        assert res.get_json()["data"]["user"]["role"] == "Customer"

    def test_manager_cannot_edit_other_managers_restaurant(self, client):
        from tests.conftest import register_and_login as ral
        from app.models import User
        other_manager_token = ral(client, email="othermgr@example.com", password="secret123")
        client.post("/api/restaurants", json={
            "name": "Other Place", "address": "Cairo", "phone": "01000000000",
        }, headers=auth_header(other_manager_token))

        # Seed manager (manager@foodify.com) owns seeded restaurants
        from app import db
        from app.seed import seed as _s
        from app.models import Restaurant
        seeded = Restaurant.query.first()
        from app.validators import generate_token
        with client.application.app_context():
            user = User.query.filter_by(Email="manager@foodify.com").first()
            seed_manager_token = generate_token(user)

        res = client.put(f"/api/restaurants/{seeded.RestaurantID}", json={
            "name": "Hijacked"
        }, headers=auth_header(other_manager_token))
        assert res.status_code == 403

    def test_admin_can_edit_any_restaurant(self, client):
        from app.models import User
        from app.validators import generate_token
        with client.application.app_context():
            admin = User.query.filter_by(Email="admin@foodify.com").first()
            admin_token = generate_token(admin)
        from app.models import Restaurant
        with client.application.app_context():
            restaurant = Restaurant.query.first()
            rid = restaurant.RestaurantID
        res = client.put(f"/api/restaurants/{rid}", json={
            "name": "Admin Edited"
        }, headers=auth_header(admin_token))
        assert res.status_code == 200
        assert res.get_json()["data"]["restaurant"]["name"] == "Admin Edited"
