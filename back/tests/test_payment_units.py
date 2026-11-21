"""Paymob adapter failure semantics with only in-process mocked responses."""

from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest

from app.payments.infrastructure.paymob import PaymobHostedGateway
from app.shared.errors import AppError
from conftest import ADDRESS
from test_payments import callback_object, mock_provider, signed_payload

pytestmark = pytest.mark.unit


def isolated_order():
    return SimpleNamespace(
        id="11111111-1111-4111-8111-111111111111", payment_method="card", currency="EGP",
        delivery_address=ADDRESS, total=Decimal("100.50"), delivery_fee=Decimal("10.00"),
        payment=SimpleNamespace(reference="isolated-order-reference"),
        items=[SimpleNamespace(item_name="Cheese Burger", unit_price=Decimal("45.25"), quantity=2)],
    )


@pytest.mark.parametrize("signature", ["", "00", "z" * 128, "0" * 128])
def test_unsigned_or_invalid_hmac_cannot_settle_payment(settings, signature):
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).verify_callback({"type": "TRANSACTION", "obj": callback_object()}, signature)
    assert raised.value.code == "invalid_payment_signature"


def test_missing_signed_field_is_invalid_callback(settings):
    payload, signature = signed_payload(settings)
    del payload["obj"]["source_data"]["pan"]
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).verify_callback(payload, signature)
    assert raised.value.code == "invalid_payment_callback"


def test_signed_provider_error_cannot_mark_payment_paid(settings):
    payload, signature = signed_payload(settings, callback_object(error_occured=True))
    assert PaymobHostedGateway(settings).verify_callback(payload, signature).status == "failed"


def test_capture_is_settlement_and_authorization_alone_is_not(settings):
    payload, signature = signed_payload(settings, callback_object(is_capture=True, is_standalone_payment=False))
    assert PaymobHostedGateway(settings).verify_callback(payload, signature).status == "paid"


@pytest.mark.parametrize("changes", [
    {"client_secret": ""}, {"id": ""}, {"intention_order_id": -1},
    {"intention_order_id": True}, {"intention_order_id": "9001"},
])
def test_malformed_success_response_is_uncertain_and_must_not_be_retried(settings, monkeypatch, changes):
    body = {"client_secret": "one-time-secret", "id": "intention-1", "intention_order_id": 9001, **changes}
    mock_provider(monkeypatch, lambda request: httpx.Response(201, json=body))
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).create_checkout(isolated_order(), "test@example.com")
    assert raised.value.code == "payment_initialization_unknown"


def test_provider_timeout_has_unknown_outcome(settings, monkeypatch):
    def timeout(request):
        raise httpx.ReadTimeout("isolated timeout", request=request)

    mock_provider(monkeypatch, timeout)
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).create_checkout(isolated_order(), "test@example.com")
    assert raised.value.code == "payment_initialization_unknown"


def test_inconsistent_order_total_is_rejected_before_contacting_provider(settings, monkeypatch):
    def unexpected_request(request):
        raise AssertionError("An inconsistent total must never reach a payment provider.")

    mock_provider(monkeypatch, unexpected_request)
    order = isolated_order()
    order.total = Decimal("1.00")
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).create_checkout(order, "test@example.com")
    assert raised.value.code == "payment_setup_rejected"
