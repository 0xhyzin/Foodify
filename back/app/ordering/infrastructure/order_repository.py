"""Owned and bounded order reads; payment and lines load in bounded batches."""

from sqlalchemy import select
from sqlalchemy.orm import Session, attributes, selectinload

from app.ordering.models import FoodOrder, FoodOrderItem, OrderEvent, Payment, PaymentEvent


class SqlAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _query():
        return select(FoodOrder).options(
            selectinload(FoodOrder.items), selectinload(FoodOrder.payment)
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

    def list_for_restaurant(self, restaurant_id: str, limit: int, offset: int) -> list[FoodOrder]:
        return list(
            self.session.scalars(
                self._query()
                .where(FoodOrder.restaurant_id == restaurant_id)
                .order_by(FoodOrder.created_at.desc(), FoodOrder.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
