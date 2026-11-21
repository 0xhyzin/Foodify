"""Dependency injection factories for notifications."""

from typing import Annotated

from fastapi import Depends

from app.notifications.dispatcher import SqlAlchemyNotificationDispatcher
from app.notifications.interfaces import (
    NotificationDispatcherInterface,
    NotificationRepositoryInterface,
)
from app.notifications.repository import SqlAlchemyNotificationRepository
from app.users.shared.dependencies.resources import DB


def get_notification_repository(db: DB) -> NotificationRepositoryInterface:
    return SqlAlchemyNotificationRepository(db)


def get_notification_dispatcher(db: DB) -> NotificationDispatcherInterface:
    return SqlAlchemyNotificationDispatcher(db)


NotificationRepo = Annotated[
    NotificationRepositoryInterface, Depends(get_notification_repository)
]
Notifications = Annotated[
    NotificationDispatcherInterface, Depends(get_notification_dispatcher)
]
