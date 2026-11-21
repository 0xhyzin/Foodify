"""Sprint 3 notifications (all 10 events), failure resilience, and payment failure consistency."""

import pytest
from sqlalchemy import select

from app.notifications.dispatcher import build_notification_content
from app.ordering.models import Notification
from conftest import auth_header, register_and_login
from test_ordering import add_item, checkout
from test_payments import callback_object, post_callback, prepare_order
from test_restaurants import REST
from test_sprint3_delivery import create_cash_order, user_id


@pytest.mark.unit
@pytest.mark.parametrize(
    "event_type",
    [
        "order_accepted",
        "order_rejected",
        "order_preparing",
        "order_ready_for_pickup",
        "delivery_assigned",
        "delivery_reassigned",
        "order_picked_up",
        "order_delivered",
        "payment_failed",
        "order_cancelled",
        "order_assigned_to_preparer",
        "order_ready_for_courier_pickup",
    ],
)
def test_notification_templates_cover_all_sprint3_events(event_type):
    title, message = build_notification_content(
        event_type, "12345678-1111-4111-8111-111111111111", {"note": "Detail"}
    )
    assert title and "12345678" in message and "Detail" in message


@pytest.mark.integration
def test_all_fulfillment_and_delivery_notifications_and_isolation(
    client, customer, restaurant_manager, courier, second_courier, address
):
    order = create_cash_order(client, customer, address)
    c1_id = user_id(client, courier)
    c2_id = user_id(client, second_courier)
    op_url = f"/api/v1/operations/orders/{order['id']}/status"

    # Manager transitions: accepted -> preparing -> ready_for_pickup (3 customer notifications).
    for status in ("accepted", "preparing", "ready_for_pickup"):
        assert client.patch(op_url, json={"status": status}, headers=restaurant_manager).status_code == 200

    # Assign courier 1 & reassign courier 2.
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/delivery-assignment",
            json={"delivery_person_id": c1_id},
            headers=restaurant_manager,
        ).status_code
        == 201
    )
    assert (
        client.patch(
            f"/api/v1/orders/{order['id']}/delivery-assignment",
            json={"new_delivery_person_id": c2_id},
            headers=restaurant_manager,
        ).status_code
        == 200
    )

    # Courier 2 picks up and delivers (2 customer notifications).
    del_url = f"/api/v1/delivery/orders/{order['id']}/status"
    assert client.patch(del_url, json={"status": "PICKED_UP"}, headers=second_courier).status_code == 200
    assert client.patch(del_url, json={"status": "DELIVERED"}, headers=second_courier).status_code == 200

    # Verify customer notifications.
    cust_res = client.get("/api/v1/notifications", headers=customer).json()["data"]
    assert cust_res["unread_count"] == 5
    assert [n["event_type"] for n in reversed(cust_res["notifications"])] == [
        "order_accepted",
        "order_preparing",
        "order_ready_for_pickup",
        "order_picked_up",
        "order_delivered",
    ]
    assert all(n["delivery_status"] == "sent" for n in cust_res["notifications"])

    # Verify courier 1 and courier 2 notifications.
    c1_notifs = client.get("/api/v1/notifications", headers=courier).json()["data"]["notifications"]
    c2_notifs = client.get("/api/v1/notifications", headers=second_courier).json()["data"][
        "notifications"
    ]
    assert [n["event_type"] for n in c1_notifs] == ["delivery_assigned"]
    assert [n["event_type"] for n in c2_notifs] == ["delivery_reassigned"]

    # Another user cannot mark customer's notification as read -> 404.
    notif_id = cust_res["notifications"][0]["id"]
    stranger = auth_header(register_and_login(client, email="stranger-notif@example.com"))
    assert client.patch(f"/api/v1/notifications/{notif_id}/read", headers=stranger).status_code == 404

    # Mark one read, filter unread_only, then mark all read.
    marked = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=customer)
    assert marked.status_code == 200 and marked.json()["data"]["notification"]["read_at"] is not None
    unread = client.get("/api/v1/notifications?unread_only=true", headers=customer).json()["data"]
    assert unread["unread_count"] == 4 and len(unread["notifications"]) == 4

    read_all = client.post("/api/v1/notifications/read-all", headers=customer)
    assert read_all.status_code == 200 and read_all.json()["data"]["updated_count"] == 4
    assert client.get("/api/v1/notifications", headers=customer).json()["data"]["unread_count"] == 0


@pytest.mark.integration
def test_rejection_and_cancellation_emit_expected_notifications(
    client, customer, restaurant_manager, address
):
    rejected_order = create_cash_order(client, customer, address)
    assert (
        client.patch(
            f"/api/v1/operations/orders/{rejected_order['id']}/status",
            json={"status": "rejected", "note": "Kitchen closed"},
            headers=restaurant_manager,
        ).status_code
        == 200
    )

    cancelled_order = create_cash_order(client, customer, address)
    assert (
        client.post(f"/api/v1/orders/{cancelled_order['id']}/cancel", headers=customer).status_code
        == 200
    )

    notifs = client.get("/api/v1/notifications", headers=customer).json()["data"]["notifications"]
    events = {n["order_id"]: n["event_type"] for n in notifs}
    assert events == {
        rejected_order["id"]: "order_rejected",
        cancelled_order["id"]: "order_cancelled",
    }


@pytest.mark.integration
def test_notification_dispatch_failure_does_not_corrupt_order_transition(
    client, customer, restaurant_manager, address, monkeypatch
):
    order = create_cash_order(client, customer, address)

    def broken_dispatch(self, event_type, order_id, recipient_id, details=None):
        # SqlAlchemyNotificationDispatcher itself catches & rolls back inside dispatch;
        # verify even if internal content/session raises, order commit survives.
        raise RuntimeError("Simulated notification channel outage")

    from app.notifications.dispatcher import SqlAlchemyNotificationDispatcher

    monkeypatch.setattr(
        "app.notifications.dispatcher.build_notification_content",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Simulated outage")),
    )
    # Call real dispatcher -> must swallow error safely after order commit.
    res = client.patch(
        f"/api/v1/operations/orders/{order['id']}/status",
        json={"status": "accepted"},
        headers=restaurant_manager,
    )
    assert res.status_code == 200, res.text
    assert res.json()["data"]["order"]["status"] == "accepted"

    saved = client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]
    assert saved["status"] == "accepted"
    assert client.get("/api/v1/notifications", headers=customer).json()["data"]["notifications"] == []
    assert isinstance(SqlAlchemyNotificationDispatcher, type)


@pytest.mark.integration
def test_payment_failure_notifies_customer_blocks_fulfillment_and_allows_retry(
    client, customer, operator, address, db, settings, monkeypatch
):
    order = prepare_order(client, customer, address, db)
    failed = post_callback(client, settings, callback_object(id=8001, success=False))
    assert failed.status_code == 200

    current = client.get(f"/api/v1/orders/{order['id']}", headers=customer).json()["data"]["order"]
    assert current["status"] == "awaiting_payment"
    assert current["payment_status"] == "failed"
    assert current["events"][-1]["status"] == "payment_failed"

    # Manager cannot accept an order whose payment failed.
    accept = client.patch(
        f"/api/v1/operations/orders/{order['id']}/status",
        json={"status": "accepted"},
        headers=operator,
    )
    assert accept.status_code == 409 and accept.json()["error"]["code"] == "payment_not_confirmed"

    # Customer receives payment_failed notification.
    notifs = client.get("/api/v1/notifications", headers=customer).json()["data"]["notifications"]
    assert [n["event_type"] for n in notifs] == ["payment_failed"]

    # Customer can retry payment without creating a duplicate order.
    from datetime import timedelta
    from app.payments.shared.interfaces import HostedCheckout
    from app.shared.time import utcnow

    monkeypatch.setattr(
        "app.payments.infrastructure.paymob.PaymobHostedGateway.create_checkout",
        lambda self, ord_, email: HostedCheckout(
            url="https://eg.checkout.paymob.com/unified?publicKey=pk&clientSecret=retry",
            provider_order_id="9009",
            intention_id="intention-retry",
            encrypted_token="enc-retry",
            expires_at=utcnow() + timedelta(minutes=15),
        ),
    )
    retry = client.post(f"/api/v1/orders/{order['id']}/payment", headers=customer)
    assert retry.status_code == 200, retry.text
    assert "clientSecret=retry" in retry.json()["data"]["checkout_url"]


@pytest.mark.integration
def test_rejected_instapay_transfer_emits_payment_failed_notification(
    client, customer, operator, address
):
    add_item(client, customer)
    order = checkout(client, customer, address, method="instapay").json()["data"]["order"]
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/transfer-claim",
            json={"reference": "CLAIM-REJECT-1"},
            headers=customer,
        ).status_code
        == 200
    )
    review = client.post(
        f"/api/v1/operations/orders/{order['id']}/transfer-review",
        json={
            "decision": "reject",
            "verified_reference": "BANK-NONE-1",
            "note": "Transfer not found in statement",
        },
        headers=operator,
    )
    assert review.status_code == 200
    assert review.json()["data"]["order"]["payment_status"] == "rejected"
    assert review.json()["data"]["order"]["status"] == "awaiting_payment"

    notifs = client.get("/api/v1/notifications", headers=customer).json()["data"]["notifications"]
    assert [n["event_type"] for n in notifs] == ["payment_failed"]
