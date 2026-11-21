"""Business rules in isolation: no HTTP app, SQL session or external provider."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.ordering.shared.mappers import cart_response
from app.ordering.shared.pricing import money
from app.users.browser.verify_email.service import VerifyBrowserEmailService
from app.users.verify_email.dto import VerifyEmailRequest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("value,expected", [
    ("12.345", "12.35"), ("12.344", "12.34"), ("0.005", "0.01"), ("0", "0.00"),
])
def test_money_rounds_at_the_currency_boundary(value, expected):
    assert money(Decimal(value)) == Decimal(expected)


def test_empty_cart_does_not_charge_delivery():
    cart = cart_response(None, delivery_fee=Decimal("99.00")).data.cart
    assert cart.items == [] and cart.total == Decimal("0.00")
    assert cart.delivery_fee == Decimal("0.00")


@pytest.mark.parametrize("restaurant_active,available", [(True, True), (False, False)])
def test_cart_mapping_uses_decimal_quantities_and_restaurant_availability(restaurant_active, available):
    menu = SimpleNamespace(id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", name="Burger",
                           price=Decimal("45.25"), image=None, is_available=True)
    cart = SimpleNamespace(id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                           restaurant_id="11111111-1111-4111-8111-111111111111", revision=7,
                           items=[SimpleNamespace(id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                                                  menu_item=menu, quantity=2)])
    view = cart_response(cart, Decimal("10.00"), restaurant_active).data.cart
    assert view.subtotal == Decimal("90.50") and view.total == Decimal("100.50")
    assert view.items[0].available is available


@pytest.mark.parametrize("fail_at", [None, "issuer", "commit"])
def test_confirmation_transaction_commits_only_with_issued_session(fail_at):
    user = SimpleNamespace(id="isolated-user", is_email_verified=False)
    token = SimpleNamespace(consumed_at=None)
    calls = []
    response = object()

    class EmailActions:
        def require_action(self, raw, kind):
            assert raw == "isolated-email-proof-0123456789abcdef" and kind == "verify_email"
            return user, token

    class Actions:
        def invalidate(self, user_id, kind):
            calls.append("invalidate")

    class Issuer:
        def create_session(self, owner):
            calls.append("issue")
            assert owner.is_email_verified and token.consumed_at is not None
            if fail_at == "issuer":
                raise RuntimeError("isolated issuer failure")
            return response

    class Uow:
        def commit(self):
            calls.append("commit")
            if fail_at == "commit":
                raise RuntimeError("isolated commit failure")

        def rollback(self):
            calls.append("rollback")

    service = VerifyBrowserEmailService(EmailActions(), Actions(), Issuer(), Uow())
    payload = VerifyEmailRequest(token="isolated-email-proof-0123456789abcdef")
    if fail_at:
        with pytest.raises(RuntimeError):
            service.execute(payload)
        assert calls[-1] == "rollback"
    else:
        assert service.execute(payload) is response
        assert calls == ["invalidate", "issue", "commit"]
