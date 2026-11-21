"""Ports for dispatching and querying in-app notifications."""

from typing import Protocol

from app.ordering.models import Notification


class NotificationDispatcherInterface(Protocol):
    def dispatch(
        self,
        event_type: str,
        order_id: str,
        recipient_id: str,
        details: dict[str, str] | None = None,
    ) -> None: ...


class NotificationRepositoryInterface(Protocol):
    def list_for_user(
        self, user_id: str, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]: ...

    def count_unread(self, user_id: str) -> int: ...

    def get_owned(self, notification_id: str, user_id: str) -> Notification | None: ...

    def mark_read(self, notification: Notification) -> Notification: ...

    def mark_all_read(self, user_id: str) -> int: ...
