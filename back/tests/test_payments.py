"""Hosted payment setup, signed callbacks and manual transfer settlement.

Every provider response is mocked. No card data, real intention or transfer is sent.
"""

import hashlib
import hmac
import json
from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import func, select

from app.ordering.models import FoodOrder, Payment, PaymentEvent
from app.payments.infrastructure.paymob import PaymobHostedGateway
from app.payments.shared.interfaces import HostedCheckout
from app.shared.errors import AppError
from app.shared.time import utcnow
from conftest import auth_header, register_and_login
from test_ordering import add_item, checkout
from test_restaurants import REST


def callback_object(**changes):
    return {
        "id": 7001, "amount_cents": 10050, "created_at": "2026-11-01T10:00:00Z",
        "currency": "EGP", "error_occured": False, "has_parent_transaction": False,
        "integration_id": 101, "is_3d_secure": True, "is_auth": False,
        "is_capture": False, "is_refunded": False, "is_standalone_payment": True,
        "is_voided": False, "order": {"id": 9001}, "owner": 100,
        "pending": False, "source_data": {"pan": "2346", "sub_type": "MasterCard", "type": "card"},
        "success": True, **changes,
    }


def signed_payload(settings, obj=None):
    obj = obj or callback_object()
    # Independent fixture of Paymob's documented field ordering.
    values = [obj["amount_cents"], obj["created_at"], obj["currency"], obj["error_occured"],
              obj["has_parent_transaction"], obj["id"], obj["integration_id"], obj["is_3d_secure"],
              obj["is_auth"], obj["is_capture"], obj["is_refunded"], obj["is_standalone_payment"],
              obj["is_voided"], obj["order"]["id"], obj["owner"], obj["pending"],
              obj["source_data"]["pan"], obj["source_data"]["sub_type"], obj["source_data"]["type"], obj["success"]]
    canonical = "".join(str(value).lower() if isinstance(value, bool) else str(value) for value in values)
    signature = hmac.new(settings.paymob_hmac_secret.get_secret_value().encode(), canonical.encode(), hashlib.sha512).hexdigest()
    return {"type": "TRANSACTION", "obj": obj}, signature


def prepare_order(client, customer, address, db):
    add_item(client, customer)
    order = checkout(client, customer, address, method="card").json()["data"]["order"]
    payment = db.scalar(select(Payment).where(Payment.order_id == order["id"]))
    payment.provider_order_id = "9001"
    db.commit()
    return order


def post_callback(client, settings, obj=None):
    payload, signature = signed_payload(settings, obj)
    return client.post("/api/v1/payments/paymob/callback?hmac=" + signature, json=payload)


@pytest.mark.parametrize("changes,expected", [
    ({}, "paid"), ({"pending": True}, "pending"), ({"success": False}, "failed"),
    ({"is_auth": True, "is_standalone_payment": False}, "failed"),
    ({"is_refunded": True}, "refunded"), ({"is_voided": True}, "refunded"),
])
@pytest.mark.unit
def test_signed_callback_status_rules(settings, changes, expected):
    payload, signature = signed_payload(settings, callback_object(**changes))
    assert PaymobHostedGateway(settings).verify_callback(payload, signature).status == expected


@pytest.mark.unit
def test_tampering_with_signed_amount_is_rejected(settings):
    payload, signature = signed_payload(settings)
    payload["obj"]["amount_cents"] += 1
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).verify_callback(payload, signature)
    assert raised.value.code == "invalid_payment_signature"


@pytest.mark.parametrize("changes", [{"success": "true"}, {"amount_cents": True}, {"id": -1}])
@pytest.mark.unit
def test_signed_but_malformed_callback_types_rejected(settings, changes):
    payload, signature = signed_payload(settings, callback_object(**changes))
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).verify_callback(payload, signature)
    assert raised.value.code == "invalid_payment_callback"


@pytest.mark.integration
def test_duplicate_callback_settles_once_and_clears_unchanged_cart(client, customer, address, db, settings):
    order = prepare_order(client, customer, address, db)
    assert post_callback(client, settings).status_code == 200
    assert post_callback(client, settings).status_code == 200
    result = client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]
    assert result["status"] == "pending" and result["payment_status"] == "paid"
    assert result["payment"]["transaction_id"]
    assert result["payment"]["provider_transaction_id"] == "7001"
    assert len(result["events"]) == 2
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(PaymentEvent)) == 1
    assert client.get(f"/api/v1/carts/{REST}", headers=customer).json()["data"]["cart"]["items"] == []


@pytest.mark.integration
def test_settlement_preserves_cart_changed_during_payment(client, customer, address, db, settings):
    prepare_order(client, customer, address, db)
    add_item(client, customer, quantity=1)
    assert post_callback(client, settings).status_code == 200
    assert client.get(f"/api/v1/carts/{REST}", headers=customer).json()["data"]["cart"]["items"][0]["quantity"] == 3


@pytest.mark.parametrize("changes", [{"amount_cents": 1}, {"currency": "USD"}, {"integration_id": 999}])
@pytest.mark.integration
def test_signed_callback_must_match_recorded_order(client, customer, address, db, settings, changes):
    order = prepare_order(client, customer, address, db)
    response = post_callback(client, settings, callback_object(**changes))
    assert response.status_code == 409 and response.json()["error"]["code"] == "payment_mismatch"
    assert client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]["payment_status"] == "pending"


@pytest.mark.integration
def test_late_failure_cannot_revert_paid_order(client, customer, address, db, settings):
    order = prepare_order(client, customer, address, db)
    assert post_callback(client, settings).status_code == 200
    assert post_callback(client, settings, callback_object(success=False)).status_code == 200
    assert client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]["payment_status"] == "paid"


@pytest.mark.integration
def test_second_settled_transaction_requires_reconciliation(client, customer, address, db, settings):
    prepare_order(client, customer, address, db)
    assert post_callback(client, settings).status_code == 200
    response = post_callback(client, settings, callback_object(id=7002))
    assert response.status_code == 409 and response.json()["error"]["code"] == "duplicate_payment"


@pytest.mark.integration
def test_browser_return_query_cannot_mark_order_paid(client, customer, address, db):
    order = prepare_order(client, customer, address, db)
    response = client.get(f"/api/v1/payments/return/{order['id']}?success=true&paid=true", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"http://127.0.0.1:5173/#/orders/{order['id']}"
    assert client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]["payment_status"] == "pending"


def mock_provider(monkeypatch, handler):
    real_client = httpx.Client
    monkeypatch.setattr("app.payments.infrastructure.paymob.httpx.Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))


@pytest.mark.integration
def test_paymob_item_quantities_produce_exact_total_and_encrypted_checkout(client, customer, address, db, settings, monkeypatch):
    prepare_order(client, customer, address, db)
    order = db.scalar(select(FoodOrder))
    from app.ordering.infrastructure.order_repository import SqlAlchemyOrderRepository
    order = SqlAlchemyOrderRepository(db).get_owned(order.id, order.user_id)
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        assert request.url == "https://accept.paymob.com/v1/intention/"
        return httpx.Response(201, json={"id": "intention-test", "intention_order_id": 12345, "client_secret": "one-use-secret"})

    mock_provider(monkeypatch, handler)
    result = PaymobHostedGateway(settings).create_checkout(order, "test@example.com")
    request = requests[0]
    assert request["amount"] == 10050
    assert sum(item["amount"] * item["quantity"] for item in request["items"]) == request["amount"]
    assert request["items"][0]["amount"] == 9050 and request["items"][0]["quantity"] == 1
    assert "2" in request["items"][0]["name"]
    assert result.encrypted_token != "one-use-secret" and "one-use-secret" not in result.encrypted_token
    parts = urlsplit(result.url)
    assert parts.scheme == "https" and parts.hostname == "eg.checkout.paymob.com"
    assert parse_qs(parts.query)["clientSecret"] == ["one-use-secret"]


@pytest.mark.parametrize("status,code", [(400, "payment_setup_rejected"), (401, "payment_setup_rejected"), (406, "payment_setup_rejected"), (500, "payment_initialization_unknown")])
@pytest.mark.integration
def test_provider_rejection_and_uncertain_outcomes_differ(client, customer, address, db, settings, monkeypatch, status, code):
    prepare_order(client, customer, address, db)
    from app.ordering.infrastructure.order_repository import SqlAlchemyOrderRepository
    saved = db.scalar(select(FoodOrder))
    order = SqlAlchemyOrderRepository(db).get_owned(saved.id, saved.user_id)
    mock_provider(monkeypatch, lambda request: httpx.Response(status, json={"detail": "secret provider diagnostic"}))
    with pytest.raises(AppError) as raised:
        PaymobHostedGateway(settings).create_checkout(order, "test@example.com")
    assert raised.value.code == code
    assert "secret provider diagnostic" not in raised.value.message


@pytest.mark.parametrize("code,state", [("payment_setup_rejected", "pending"), ("payment_initialization_unknown", "initialization_unknown")])
@pytest.mark.integration
def test_payment_service_does_not_retry_uncertain_intentions(client, customer, address, db, monkeypatch, code, state):
    order = prepare_order(client, customer, address, db)
    calls = []

    def fail(*args):
        calls.append(1)
        raise AppError(code, "Provider unavailable", 503)

    monkeypatch.setattr(PaymobHostedGateway, "create_checkout", fail)
    endpoint = f"/api/v1/orders/{order['id']}/payment"
    assert client.post(endpoint, headers=customer).status_code == 503
    db.expire_all()
    assert db.scalar(select(Payment)).status == state
    if state == "initialization_unknown":
        assert client.post(endpoint, headers=customer).status_code == 409
        assert len(calls) == 1


@pytest.mark.integration
def test_existing_checkout_is_reopened_without_new_intention(client, customer, address, db, settings, monkeypatch):
    order = prepare_order(client, customer, address, db)
    from cryptography.fernet import Fernet
    payment = db.scalar(select(Payment))
    payment.checkout_token = Fernet(settings.email_encryption_key.get_secret_value().encode()).encrypt(b"existing-one-time-secret").decode()
    payment.expires_at = utcnow() + timedelta(minutes=10)
    db.commit()

    def fail(*args):
        raise AssertionError("A reusable intention must not create another intention.")

    monkeypatch.setattr(PaymobHostedGateway, "create_checkout", fail)
    response = client.post(f"/api/v1/orders/{order['id']}/payment", headers=customer)
    assert response.status_code == 200
    assert urlsplit(response.json()["data"]["checkout_url"]).hostname == "eg.checkout.paymob.com"


@pytest.mark.integration
def test_customer_claim_is_not_payment_confirmation(client, customer, operator, address):
    add_item(client, customer)
    order = checkout(client, customer, address, method="instapay").json()["data"]["order"]
    endpoint = f"/api/v1/orders/{order['id']}/transfer-claim"
    claimed = client.post(endpoint, json={"reference": "CLAIM-123456"}, headers=customer)
    assert claimed.status_code == 200
    assert claimed.json()["data"]["order"]["payment_status"] == "pending_review"
    review = f"/api/v1/operations/orders/{order['id']}/transfer-review"
    payload = {"decision": "approve", "verified_reference": "BANK-123456", "note": "Matched with bank record"}
    assert client.post(review, json=payload, headers=customer).status_code == 403
    approved = client.post(review, json=payload, headers=operator)
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["order"]["payment_status"] == "paid"
    assert approved.json()["data"]["order"]["status"] == "pending"
    assert approved.json()["data"]["order"]["payment"]["transaction_id"]


@pytest.mark.unit
def test_simulation_is_disabled_in_production(settings):
    from app.ordering.infrastructure.payments import ConfiguredPaymentGateway, SimulatedPaymentGateway
    with pytest.raises(AppError):
        SimulatedPaymentGateway("production", True).authorize(Decimal("10.00"), "simulated")
    production = settings.model_copy(update={"app_env": "production", "allow_simulated_payments": True})
    assert next(item for item in ConfiguredPaymentGateway(production).methods() if item["code"] == "simulated")["enabled"] is False


@pytest.mark.integration
def test_unknown_provider_order_requests_callback_retry_without_writing_event(client, db, settings):
    response = post_callback(client, settings)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "payment_not_found"
    assert db.scalar(select(func.count()).select_from(PaymentEvent)) == 0


@pytest.mark.integration
def test_refund_must_match_settled_transaction_and_does_not_corrupt_payment(client, customer, address, db, settings):
    order = prepare_order(client, customer, address, db)
    assert post_callback(client, settings).status_code == 200
    response = post_callback(client, settings, callback_object(id=7002, is_refunded=True))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "payment_transaction_mismatch"
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(PaymentEvent)) == 1
    assert client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]["payment_status"] == "paid"


@pytest.mark.integration
def test_refund_callback_is_idempotent_and_cannot_be_undone_by_paid_callback(client, customer, address, db, settings):
    order = prepare_order(client, customer, address, db)
    assert post_callback(client, settings).status_code == 200
    refund = callback_object(is_refunded=True)
    assert post_callback(client, settings, refund).status_code == 200
    assert post_callback(client, settings, refund).status_code == 200
    assert post_callback(client, settings).status_code == 200
    result = client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]
    assert result["payment_status"] == "refunded" and len(result["events"]) == 3
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(PaymentEvent)) == 2


@pytest.mark.integration
def test_another_customer_cannot_start_or_claim_payment_for_owned_order(client, customer, address, db):
    order = prepare_order(client, customer, address, db)
    stranger = auth_header(register_and_login(client, email="stranger@example.com"))
    assert client.post(f"/api/v1/orders/{order['id']}/payment", headers=stranger).status_code == 404
    assert client.post(f"/api/v1/orders/{order['id']}/transfer-claim", json={"reference": "CLAIM-123456"}, headers=stranger).status_code == 404


@pytest.mark.integration
def test_bank_transaction_reference_cannot_settle_two_orders(client, customer, operator, address):
    orders = []
    for reference in ["CLAIM-123456", "CLAIM-987654"]:
        add_item(client, customer)
        order = checkout(client, customer, address, method="instapay").json()["data"]["order"]
        assert client.post(f"/api/v1/orders/{order['id']}/transfer-claim", json={"reference": reference}, headers=customer).status_code == 200
        orders.append(order)
    payload = {"decision": "approve", "verified_reference": "BANK-123456", "note": "Matched with bank record"}
    assert client.post(f"/api/v1/operations/orders/{orders[0]['id']}/transfer-review", json=payload, headers=operator).status_code == 200
    duplicate = client.post(f"/api/v1/operations/orders/{orders[1]['id']}/transfer-review", json=payload, headers=operator)
    assert duplicate.status_code == 409
    untouched = client.get(f"/api/v1/orders/{orders[1]['id']}", headers=customer).json()["data"]["order"]
    assert untouched["payment_status"] == "pending_review" and untouched["status"] == "awaiting_payment"


@pytest.mark.integration
def test_provider_transaction_identifier_cannot_settle_two_orders(client, customer, address, db, settings):
    prepare_order(client, customer, address, db)
    add_item(client, customer)
    second = checkout(client, customer, address, method="card").json()["data"]["order"]
    db.scalar(select(Payment).where(Payment.order_id == second["id"])).provider_order_id = "9002"
    db.commit()
    assert post_callback(client, settings).status_code == 200
    reused = callback_object(order={"id": 9002}, amount_cents=int(Decimal(second["total"]) * 100))
    replay = post_callback(client, settings, reused)
    # The global transaction/status event identifier is already consumed; the
    # callback is acknowledged without settling another order.
    assert replay.status_code == 200
    result = client.get(f"/api/v1/orders/{second['id']}", headers=customer).json()["data"]["order"]
    assert result["payment_status"] == "pending" and result["status"] == "awaiting_payment"
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(PaymentEvent)) == 1
