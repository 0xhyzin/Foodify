"""Public DTO contracts for Sprint 3 notifications."""

from datetime import UTC, datetime

from app.ordering.models import Notification
from app.ordering.shared.dto import Pagination
from app.shared.dto import APIModel


class NotificationView(APIModel):
    id: str
    order_id: str
    event_type: str
    channel: str
    title: str
    message: str
    delivery_status: str
    read_at: datetime | None
    created_at: datetime


class NotificationData(APIModel):
    notification: NotificationView


class NotificationResponse(APIModel):
    data: NotificationData


class NotificationListData(APIModel):
    notifications: list[NotificationView]
    unread_count: int
    pagination: Pagination


class NotificationListResponse(APIModel):
    data: NotificationListData


class ReadAllData(APIModel):
    updated_count: int


class ReadAllResponse(APIModel):
    data: ReadAllData


def notification_view(item: Notification) -> NotificationView:
    return NotificationView(
        id=item.id,
        order_id=item.order_id,
        event_type=item.event_type,
        channel=item.channel,
        title=item.title,
        message=item.message,
        delivery_status=item.delivery_status,
        read_at=item.read_at.replace(tzinfo=UTC) if item.read_at else None,
        created_at=item.created_at.replace(tzinfo=UTC),
    )
