"""TC-04 Restaurants (FR-08) and TC-05 Menu (FR-09)."""


class TestRestaurantListing:
    # ---------- Positive ----------
    def test_list_returns_all_seeded_restaurants(self, client):
        res = client.get("/api/restaurants")
        assert res.status_code == 200
        assert len(res.get_json()["data"]["restaurants"]) == 3

    def test_list_includes_fields_needed_by_frontend_card(self, client):
        r = client.get("/api/restaurants").get_json()["data"]["restaurants"][0]
        for field in ("id", "name", "category", "rating", "reviews", "time", "address", "image"):
            assert field in r

    def test_filter_by_burger_category(self, client):
        res = client.get("/api/restaurants?category=burger")
        names = [r["name"] for r in res.get_json()["data"]["restaurants"]]
        assert names == ["برجر ماستر - Burger Master"]

    def test_search_by_partial_name(self, client):
        res = client.get("/api/restaurants?search=burger")
        assert len(res.get_json()["data"]["restaurants"]) == 1

    def test_search_case_insensitive(self, client):
        res = client.get("/api/restaurants?search=BURGER")
        assert len(res.get_json()["data"]["restaurants"]) == 1

    def test_filter_and_search_combine(self, client):
        res = client.get("/api/restaurants?category=pizza&search=heat")
        assert len(res.get_json()["data"]["restaurants"]) == 1

    # ---------- Negative / edge ----------
    def test_unknown_category_returns_empty_list(self, client):
        res = client.get("/api/restaurants?category=sushi")
        assert res.status_code == 200
        assert res.get_json()["data"]["restaurants"] == []

    def test_no_match_search_returns_empty_list(self, client):
        res = client.get("/api/restaurants?search=zzzz")
        assert res.status_code == 200
        assert res.get_json()["data"]["restaurants"] == []


class TestRestaurantDetails:
    def test_get_details_returns_menu_categories(self, client):
        res = client.get("/api/restaurants/1")
        assert res.status_code == 200
        r = res.get_json()["data"]["restaurant"]
        assert len(r["categories"]) == 4

    def test_get_nonexistent_restaurant_returns_404(self, client):
        res = client.get("/api/restaurants/9999")
        assert res.status_code == 404
        assert res.get_json()["error"]["code"] == "NOT_FOUND"

    def test_get_categories_endpoint(self, client):
        res = client.get("/api/restaurants/2/categories")
        cats = res.get_json()["data"]["categories"]
        assert "بيتزا إيطالي" in cats


class TestMenu:
    def test_menu_matches_frontend_data(self, client):
        res = client.get("/api/restaurants/1/menu")
        items = res.get_json()["data"]["menu"]
        assert len(items) == 3
        names = {i["name"] for i in items}
        assert "سوبر دبل تشيز برجر" in names

    def test_menu_item_has_fields_needed_by_frontend(self, client):
        item = client.get("/api/restaurants/1/menu").get_json()["data"]["menu"][0]
        for field in ("id", "name", "category", "price", "desc", "image"):
            assert field in item

    def test_filter_menu_by_category(self, client):
        res = client.get("/api/restaurants/1/menu?category=شاورما")
        assert res.status_code == 200  # restaurant 1 has no shawarma; still 200 with []

    def test_filter_menu_by_existing_category(self, client):
        res = client.get("/api/restaurants/3/menu?category=شاورما")
        items = res.get_json()["data"]["menu"]
        assert len(items) == 1
        assert items[0]["name"] == "طبق شاورما عربي دجاج"

    def test_menu_of_nonexistent_restaurant_returns_404(self, client):
        res = client.get("/api/restaurants/9999/menu")
        assert res.status_code == 404

    def test_manager_can_add_menu_item(self, client):
        from app.models import User
        from app.validators import generate_token
        from app.models import Restaurant
        with client.application.app_context():
            user = User.query.filter_by(Email="manager@foodify.com").first()
            restaurant = Restaurant.query.first()
            rid, token = restaurant.RestaurantID, generate_token(user)
        res = client.post(f"/api/restaurants/{rid}/menu", json={
            "name": "New Item", "category": "الأكثر مبيعاً", "price": 99.5, "desc": "Test item",
        }, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 201
        assert res.get_json()["data"]["item"]["price"] == 99.5

    def test_add_menu_item_negative_price_returns_400(self, client):
        from app.models import User, Restaurant
        from app.validators import generate_token
        with client.application.app_context():
            user = User.query.filter_by(Email="manager@foodify.com").first()
            rid = Restaurant.query.first().RestaurantID
            token = generate_token(user)
        res = client.post(f"/api/restaurants/{rid}/menu", json={
            "name": "Bad", "category": "c", "price": -5,
        }, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 400

    def test_add_menu_item_missing_name_returns_400(self, client):
        from app.models import User, Restaurant
        from app.validators import generate_token
        with client.application.app_context():
            user = User.query.filter_by(Email="manager@foodify.com").first()
            rid = Restaurant.query.first().RestaurantID
            token = generate_token(user)
        res = client.post(f"/api/restaurants/{rid}/menu", json={
            "category": "c", "price": 10,
        }, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 400
