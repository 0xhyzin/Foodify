"""Post-commit, failure-isolated notification dispatcher."""

import logging

from sqlalchemy.orm import Session

from app.ordering.models import Notification
from app.shared.time import utcnow

logger = logging.getLogger(__name__)

EVENT_TEMPLATES: dict[str, tuple[str, str]] = {
    "order_accepted": (
        "Order accepted",
        "Your order has been accepted.",
    ),
    "order_rejected": (
        "Order rejected",
        "Your order has been rejected.",
    ),
    "order_preparing": (
        "Order preparing",
        "Your order is being prepared.",
    ),
    "order_ready_for_pickup": (
        "Ready for pickup",
        "Your order is ready for pickup.",
    ),
    "delivery_assigned": (
        "New delivery assigned",
        "A new order has been assigned to you.",
    ),
    "delivery_reassigned": (
        "Delivery assigned to you",
        "An order has been assigned to you.",
    ),
    "order_picked_up": (
        "Order picked up",
        "Your order has been picked up.",
    ),
    "order_delivered": (
        "Order delivered",
        "Your order has been delivered.",
    ),
    "payment_failed": (
        "Payment unsuccessful",
        "Your payment was unsuccessful.",
    ),
    "order_cancelled": (
        "Order cancelled",
        "Your order has been cancelled.",
    ),
    "order_assigned_to_preparer": (
        "New order to prepare",
        "An order is ready for you to start preparing.",
    ),
    "order_ready_for_courier_pickup": (
        "Order ready for pickup",
        "The kitchen finished preparing your assigned order; it is ready for pickup.",
    ),
}


def build_notification_content(
    event_type: str, order_id: str, details: dict[str, str] | None = None
) -> tuple[str, str]:
    """Prepare safe title and body for a Sprint 3 notification event."""
    title, base_message = EVENT_TEMPLATES.get(
        event_type, ("Order update", f"Order #{order_id[:8]} has been updated.")
    )
    short_id = order_id[:8]
    note = (details or {}).get("note", "").strip()
    restaurant = (details or {}).get("restaurant_name", "").strip()
    parts = [f"{base_message} (Order #{short_id})"]
    if restaurant:
        parts.append(f"Restaurant: {restaurant}")
    if note:
        parts.append(note[:200])
    return title, " — ".join(parts)


class SqlAlchemyNotificationDispatcher:
    def __init__(self, session: Session) -> None:
        self.session = session

    def dispatch(
        self,
        event_type: str,
        order_id: str,
        recipient_id: str,
        details: dict[str, str] | None = None,
    ) -> None:
        try:
            title, message = build_notification_content(event_type, order_id, details)
            record = Notification(
                recipient_id=recipient_id,
                order_id=order_id,
                event_type=event_type,
                channel="in_app",
                title=title,
                message=message[:500],
                delivery_status="sent",
                created_at=utcnow(),
            )
            self.session.add(record)
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.warning(
                "Notification dispatch failed for event=%s order=%s", event_type, order_id
            )
