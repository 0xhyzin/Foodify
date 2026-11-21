"""Owned and bounded order reads; payment and lines load in bounded batches."""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, attributes, selectinload

from app.infrastructure.models import User
from app.ordering.models import (
    DeliveryAssignment,
    FoodOrder,
    FoodOrderItem,
    OrderEvent,
    Payment,
    PaymentEvent,
    Restaurant,
)


class SqlAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _query():
        return select(FoodOrder).options(
            selectinload(FoodOrder.restaurant),
            selectinload(FoodOrder.assigned_preparer),
            selectinload(FoodOrder.items),
            selectinload(FoodOrder.payment),
            selectinload(FoodOrder.delivery_assignment).selectinload(
                DeliveryAssignment.delivery_person
            ),
        )

    def add(self, order: FoodOrder) -> None:
        self.session.add(order)

    def get_owned(self, order_id: str, user_id: str) -> FoodOrder | None:
        return self.session.scalar(
            self._query().where(FoodOrder.id == order_id, FoodOrder.user_id == user_id)
        )

    def get_by_checkout_key(self, user_id: str, key: str) -> FoodOrder | None:
        order = self.session.scalar(
            select(FoodOrder)
            .where(FoodOrder.user_id == user_id, FoodOrder.checkout_key == key)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self._load_locked_children(order)

    def get_locked(self, order_id: str) -> FoodOrder | None:
        order = self.session.scalar(
            select(FoodOrder)
            .where(FoodOrder.id == order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self._load_locked_children(order)

    def _load_locked_children(self, order: FoodOrder | None) -> FoodOrder | None:
        if order is not None:
            # The original auth query may have started an older repeatable-read snapshot.
            # Fetch children with current reads as well when replaying a concurrent checkout.
            items = list(
                self.session.scalars(
                    select(FoodOrderItem)
                    .where(FoodOrderItem.order_id == order.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            )
            payment = self.session.scalar(
                select(Payment)
                .where(Payment.order_id == order.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            attributes.set_committed_value(order, "items", items)
            attributes.set_committed_value(order, "payment", payment)
            events = list(
                self.session.scalars(
                    select(OrderEvent)
                    .where(OrderEvent.order_id == order.id)
                    .order_by(OrderEvent.created_at, OrderEvent.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            )
            attributes.set_committed_value(order, "events", events)
            restaurant = self.session.scalar(
                select(Restaurant).where(Restaurant.id == order.restaurant_id)
            )
            attributes.set_committed_value(order, "restaurant", restaurant)
            assignment = self.session.scalar(
                select(DeliveryAssignment)
                .options(selectinload(DeliveryAssignment.delivery_person))
                .where(DeliveryAssignment.order_id == order.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            attributes.set_committed_value(order, "delivery_assignment", assignment)
            preparer = (
                None
                if order.assigned_preparer_id is None
                else self.session.scalar(
                    select(User).where(User.id == order.assigned_preparer_id)
                )
            )
            attributes.set_committed_value(order, "assigned_preparer", preparer)
        return order

    def find_by_provider_order(self, provider_order_id: str) -> FoodOrder | None:
        return self.session.scalar(
            self._query().join(Payment).where(Payment.provider_order_id == provider_order_id)
        )

    def has_payment_event(self, event_id: str) -> bool:
        return (
            self.session.scalar(
                select(PaymentEvent.id).where(PaymentEvent.id == event_id).with_for_update()
            )
            is not None
        )

    def add_payment_event(self, event: PaymentEvent) -> None:
        self.session.add(event)

    def add_delivery_assignment(self, assignment: DeliveryAssignment) -> None:
        self.session.add(assignment)

    def list_for_user(self, user_id: str, limit: int, offset: int) -> list[FoodOrder]:
        return list(
            self.session.scalars(
                self._query()
                .where(FoodOrder.user_id == user_id)
                .order_by(FoodOrder.created_at.desc(), FoodOrder.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def list_for_restaurant(
        self, restaurant_id: str, limit: int, offset: int, status: str | None = None
    ) -> list[FoodOrder]:
        stmt = self._query().where(FoodOrder.restaurant_id == restaurant_id)
        if status:
            stmt = stmt.where(FoodOrder.status == status)
        return list(
            self.session.scalars(
                stmt.order_by(FoodOrder.created_at.desc(), FoodOrder.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def list_for_courier(
        self, delivery_person_id: str, limit: int, offset: int, status: str | None = None
    ) -> list[FoodOrder]:
        stmt = (
            self._query()
            .join(DeliveryAssignment, DeliveryAssignment.order_id == FoodOrder.id)
            .where(DeliveryAssignment.delivery_person_id == delivery_person_id)
        )
        if status:
            stmt = stmt.where(FoodOrder.status == status)
        return list(
            self.session.scalars(
                stmt.order_by(FoodOrder.created_at.desc(), FoodOrder.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def list_for_preparer(
        self,
        preparer_id: str,
        restaurant_ids: list[str] | None,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> list[FoodOrder]:
        kitchen_statuses = ("accepted", "preparing", "ready_for_pickup")
        stmt = self._query().where(FoodOrder.status.in_(kitchen_statuses))
        if status:
            stmt = stmt.where(FoodOrder.status == status)
        if restaurant_ids is not None:
            if not restaurant_ids:
                stmt = stmt.where(FoodOrder.assigned_preparer_id == preparer_id)
            else:
                stmt = stmt.where(
                    or_(
                        FoodOrder.assigned_preparer_id == preparer_id,
                        and_(
                            FoodOrder.assigned_preparer_id.is_(None),
                            FoodOrder.restaurant_id.in_(restaurant_ids),
                        ),
                    )
                )
        return list(
            self.session.scalars(
                stmt.order_by(FoodOrder.created_at.desc(), FoodOrder.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
