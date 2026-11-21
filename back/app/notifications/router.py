"""Authenticated in-app notification endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.infrastructure.models import User
from app.notifications.dependencies import NotificationRepo
from app.notifications.dto import (
    NotificationData,
    NotificationListData,
    NotificationListResponse,
    NotificationResponse,
    ReadAllData,
    ReadAllResponse,
    notification_view,
)
from app.ordering.shared.dto import Pagination
from app.shared.errors import AppError

router = APIRouter(tags=["Notifications"])
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    current_user: CurrentUser,
    repo: NotificationRepo,
    unread_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
) -> NotificationListResponse:
    items = repo.list_for_user(current_user.id, unread_only, limit + 1, offset)
    unread_count = repo.count_unread(current_user.id)
    return NotificationListResponse(
        data=NotificationListData(
            notifications=[notification_view(item) for item in items[:limit]],
            unread_count=unread_count,
            pagination=Pagination(limit=limit, offset=offset, has_more=len(items) > limit),
        )
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    repo: NotificationRepo,
) -> NotificationResponse:
    record = repo.get_owned(str(notification_id), current_user.id)
    if record is None:
        raise AppError("notification_not_found", "Notification not found.", 404)
    updated = repo.mark_read(record)
    return NotificationResponse(data=NotificationData(notification=notification_view(updated)))


@router.post("/notifications/read-all", response_model=ReadAllResponse)
def mark_all_notifications_read(
    current_user: CurrentUser,
    repo: NotificationRepo,
) -> ReadAllResponse:
    count = repo.mark_all_read(current_user.id)
    return ReadAllResponse(data=ReadAllData(updated_count=count))
