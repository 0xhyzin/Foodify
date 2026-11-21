"""SQLAlchemy repository for user notifications."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.ordering.models import Notification
from app.shared.time import utcnow


class SqlAlchemyNotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(
        self, user_id: str, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.recipient_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        return list(
            self.session.scalars(
                stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def count_unread(self, user_id: str) -> int:
        count = self.session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_id == user_id, Notification.read_at.is_(None))
        )
        return int(count or 0)

    def get_owned(self, notification_id: str, user_id: str) -> Notification | None:
        return self.session.scalar(
            select(Notification)
            .where(Notification.id == notification_id, Notification.recipient_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def mark_read(self, notification: Notification) -> Notification:
        if notification.read_at is None:
            notification.read_at = utcnow()
        self.session.commit()
        return notification

    def mark_all_read(self, user_id: str) -> int:
        result = self.session.execute(
            update(Notification)
            .where(Notification.recipient_id == user_id, Notification.read_at.is_(None))
            .values(read_at=utcnow())
        )
        self.session.commit()
        return int(result.rowcount or 0)
